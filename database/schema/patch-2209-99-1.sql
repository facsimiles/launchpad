-- Copyright 2012 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

CREATE OR REPLACE FUNCTION _ftq(text) RETURNS text
    LANGUAGE plpythonu IMMUTABLE STRICT
    AS $_$
        import re

        # I think this method would be more robust if we used a real
        # tokenizer and parser to generate the query string, but we need
        # something suitable for use as a stored procedure which currently
        # means no external dependancies.

        # Convert to Unicode
        query = args[0].decode('utf8')
        ## plpy.debug('1 query is %s' % repr(query))

        # Normalize whitespace
        query = re.sub("(?u)\s+"," ", query)

        # Convert AND, OR, NOT and - to tsearch2 punctuation
        query = re.sub(r"(?u)(?:^|\s)-([\w\(])", r" !\1", query)
        query = re.sub(r"(?u)\bAND\b", "&", query)
        query = re.sub(r"(?u)\bOR\b", "|", query)
        query = re.sub(r"(?u)\bNOT\b", " !", query)
        ## plpy.debug('2 query is %s' % repr(query))

        # Deal with unwanted punctuation. We convert strings of punctuation
        # inside words to a '-' character for the hypenation handling below
        # to deal with further. Outside of words we replace with whitespace.
        # We don't mess with -&|!()' as they are handled later.
        #punctuation = re.escape(r'`~@#$%^*+=[]{}:;"<>,.?\/')
        punctuation = r"[^\w\s\-\&\|\!\(\)']"
        query = re.sub(r"(?u)(\w)%s+(\w)" % (punctuation,), r"\1-\2", query)
        query = re.sub(r"(?u)%s+" % (punctuation,), " ", query)
        ## plpy.debug('3 query is %s' % repr(query))

        # Strip ! characters inside and at the end of a word
        query = re.sub(r"(?u)(?<=\w)[\!]+", " ", query)

        # Now that we have handle case sensitive booleans, convert to lowercase
        query = query.lower()

        # Convert foo-bar to ((foo&bar)|foobar) and foo-bar-baz to
        # ((foo&bar&baz)|foobarbaz)
        def hyphen_repl(match):
            bits = match.group(0).split("-")
            return "((%s)|%s)" % ("&".join(bits), "".join(bits))
        query = re.sub(r"(?u)\b\w+-[\w\-]+\b", hyphen_repl, query)
        ## plpy.debug('4 query is %s' % repr(query))

        # Any remaining - characters are spurious
        query = query.replace('-','')

        # Remove unpartnered bracket on the left and right
        query = re.sub(r"(?ux) ^ ( [^(]* ) \)", r"(\1)", query)
        query = re.sub(r"(?ux) \( ( [^)]* ) $", r"(\1)", query)

        # Remove spurious brackets
        query = re.sub(r"(?u)\(([^\&\|]*?)\)", r" \1 ", query)
        ## plpy.debug('5 query is %s' % repr(query))

        # Insert & between tokens without an existing boolean operator
        # ( not proceeded by (|&!
        query = re.sub(r"(?u)(?<![\(\|\&\!])\s*\(", "&(", query)
        ## plpy.debug('6 query is %s' % repr(query))
        # ) not followed by )|&
        query = re.sub(r"(?u)\)(?!\s*(\)|\||\&|\s*$))", ")&", query)
        ## plpy.debug('6.1 query is %s' % repr(query))
        # Whitespace not proceded by (|&! not followed by &|
        query = re.sub(r"(?u)(?<![\(\|\&\!\s])\s+(?![\&\|\s])", "&", query)
        ## plpy.debug('7 query is %s' % repr(query))

        # Detect and repair syntax errors - we are lenient because
        # this input is generally from users.

        # Fix unbalanced brackets
        openings = query.count("(")
        closings = query.count(")")
        if openings > closings:
            query = query + " ) "*(openings-closings)
        elif closings > openings:
            query = " ( "*(closings-openings) + query
        ## plpy.debug('8 query is %s' % repr(query))

        # Strip ' character that do not have letters on both sides
        query = re.sub(r"(?u)((?<!\w)'|'(?!\w))", "", query)

        # Brackets containing nothing but whitespace and booleans, recursive
        last = ""
        while last != query:
            last = query
            query = re.sub(r"(?u)\([\s\&\|\!]*\)", "", query)
        ## plpy.debug('9 query is %s' % repr(query))

        # An & or | following a (
        query = re.sub(r"(?u)(?<=\()[\&\|\s]+", "", query)
        ## plpy.debug('10 query is %s' % repr(query))

        # An &, | or ! immediatly before a )
        query = re.sub(r"(?u)[\&\|\!\s]*[\&\|\!]+\s*(?=\))", "", query)
        ## plpy.debug('11 query is %s' % repr(query))

        # An &,| or ! followed by another boolean.
        query = re.sub(r"(?ux) \s* ( [\&\|\!] ) [\s\&\|]+", r"\1", query)
        ## plpy.debug('12 query is %s' % repr(query))

        # Leading & or |
        query = re.sub(r"(?u)^[\s\&\|]+", "", query)
        ## plpy.debug('13 query is %s' % repr(query))

        # Trailing &, | or !
        query = re.sub(r"(?u)[\&\|\!\s]+$", "", query)
        ## plpy.debug('14 query is %s' % repr(query))

        # If we have nothing but whitespace and tsearch2 operators,
        # return NULL.
        if re.search(r"(?u)^[\&\|\!\s\(\)]*$", query) is not None:
            return None

        # Convert back to UTF-8
        query = query.encode('utf8')
        ## plpy.debug('15 query is %s' % repr(query))

        return query or None
        $_$;

CREATE OR REPLACE FUNCTION ftq(text) RETURNS pg_catalog.tsquery
    LANGUAGE plpythonu IMMUTABLE STRICT
    AS $_$
        import re

        # I think this method would be more robust if we used a real
        # tokenizer and parser to generate the query string, but we need
        # something suitable for use as a stored procedure which currently
        # means no external dependancies.

        # Convert to Unicode
        query = args[0].decode('utf8')
        ## plpy.debug('1 query is %s' % repr(query))

        # Normalize whitespace
        query = re.sub("(?u)\s+"," ", query)

        # Convert AND, OR, NOT and - to tsearch2 punctuation
        query = re.sub(r"(?u)(?:^|\s)-([\w\(])", r" !\1", query)
        query = re.sub(r"(?u)\bAND\b", "&", query)
        query = re.sub(r"(?u)\bOR\b", "|", query)
        query = re.sub(r"(?u)\bNOT\b", " !", query)
        ## plpy.debug('2 query is %s' % repr(query))

        # Deal with unwanted punctuation. We convert strings of punctuation
        # inside words to a '-' character for the hypenation handling below
        # to deal with further. Outside of words we replace with whitespace.
        # We don't mess with -&|!()' as they are handled later.
        #punctuation = re.escape(r'`~@#$%^*+=[]{}:;"<>,.?\/')
        punctuation = r"[^\w\s\-\&\|\!\(\)']"
        query = re.sub(r"(?u)(\w)%s+(\w)" % (punctuation,), r"\1-\2", query)
        query = re.sub(r"(?u)%s+" % (punctuation,), " ", query)
        ## plpy.debug('3 query is %s' % repr(query))

        # Strip ! characters inside and at the end of a word
        query = re.sub(r"(?u)(?<=\w)[\!]+", " ", query)

        # Now that we have handle case sensitive booleans, convert to lowercase
        query = query.lower()

        # Convert foo-bar to ((foo&bar)|foobar) and foo-bar-baz to
        # ((foo&bar&baz)|foobarbaz)
        def hyphen_repl(match):
            bits = match.group(0).split("-")
            return "((%s)|%s)" % ("&".join(bits), "".join(bits))
        query = re.sub(r"(?u)\b\w+-[\w\-]+\b", hyphen_repl, query)
        ## plpy.debug('4 query is %s' % repr(query))

        # Any remaining - characters are spurious
        query = query.replace('-','')

        # Remove unpartnered bracket on the left and right
        query = re.sub(r"(?ux) ^ ( [^(]* ) \)", r"(\1)", query)
        query = re.sub(r"(?ux) \( ( [^)]* ) $", r"(\1)", query)

        # Remove spurious brackets
        query = re.sub(r"(?u)\(([^\&\|]*?)\)", r" \1 ", query)
        ## plpy.debug('5 query is %s' % repr(query))

        # Insert & between tokens without an existing boolean operator
        # ( not proceeded by (|&!
        query = re.sub(r"(?u)(?<![\(\|\&\!])\s*\(", "&(", query)
        ## plpy.debug('6 query is %s' % repr(query))
        # ) not followed by )|&
        query = re.sub(r"(?u)\)(?!\s*(\)|\||\&|\s*$))", ")&", query)
        ## plpy.debug('6.1 query is %s' % repr(query))
        # Whitespace not proceded by (|&! not followed by &|
        query = re.sub(r"(?u)(?<![\(\|\&\!\s])\s+(?![\&\|\s])", "&", query)
        ## plpy.debug('7 query is %s' % repr(query))

        # Detect and repair syntax errors - we are lenient because
        # this input is generally from users.

        # Fix unbalanced brackets
        openings = query.count("(")
        closings = query.count(")")
        if openings > closings:
            query = query + " ) "*(openings-closings)
        elif closings > openings:
            query = " ( "*(closings-openings) + query
        ## plpy.debug('8 query is %s' % repr(query))

        # Strip ' character that do not have letters on both sides
        query = re.sub(r"(?u)((?<!\w)'|'(?!\w))", "", query)

        # Brackets containing nothing but whitespace and booleans, recursive
        last = ""
        while last != query:
            last = query
            query = re.sub(r"(?u)\([\s\&\|\!]*\)", "", query)
        ## plpy.debug('9 query is %s' % repr(query))

        # An & or | following a (
        query = re.sub(r"(?u)(?<=\()[\&\|\s]+", "", query)
        ## plpy.debug('10 query is %s' % repr(query))

        # An &, | or ! immediatly before a )
        query = re.sub(r"(?u)[\&\|\!\s]*[\&\|\!]+\s*(?=\))", "", query)
        ## plpy.debug('11 query is %s' % repr(query))

        # An &,| or ! followed by another boolean.
        query = re.sub(r"(?ux) \s* ( [\&\|\!] ) [\s\&\|]+", r"\1", query)
        ## plpy.debug('12 query is %s' % repr(query))

        # Leading & or |
        query = re.sub(r"(?u)^[\s\&\|]+", "", query)
        ## plpy.debug('13 query is %s' % repr(query))

        # Trailing &, | or !
        query = re.sub(r"(?u)[\&\|\!\s]+$", "", query)
        ## plpy.debug('14 query is %s' % repr(query))

        # If we have nothing but whitespace and tsearch2 operators,
        # return NULL.
        if re.search(r"(?u)^[\&\|\!\s\(\)]*$", query) is not None:
            return None

        # Convert back to UTF-8
        query = query.encode('utf8')
        ## plpy.debug('15 query is %s' % repr(query))

        p = plpy.prepare("SELECT to_tsquery('default', $1) AS x", ["text"])
        query = plpy.execute(p, [query], 1)[0]["x"]
        return query or None
        $_$;

INSERT INTO LaunchpadDatabaseRevision VALUES (2209, 99, );

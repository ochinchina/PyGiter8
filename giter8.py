#!/usr/bin/python

import os
import os.path
import random
import shutil
import sys

class TempField:
    """stands for the template field in the giter8"""
    def __init__( self, fields_value ):
        self._format_methods = { 'upper': self._upper,
                                'lower': self._lower,
                                'cap': self._capitalize,
                                'decap': self._decapitalize,
                                'start': self._startCase,
                                'word': self._word,
                                'Camel': self._upperCamel,
                                'camel': self._lowerCamel,
                                'hypen': self._hyphen,
                                'norm': self._normalize,
                                'snake': self._snake,
                                'packaged': self._packaged,
                                'random': self._random }
        self._fields_value = fields_value
        self.WORD_LETTERS = map(lambda c: chr(c), range(ord('a'), ord('z')))
        self.WORD_LETTERS.extend( map(lambda c: chr(c), range(ord('A'), ord('Z'))) )
        self.WORD_LETTERS.extend( map(lambda c: chr(c), range(ord('0'), ord('9'))) )
        self.WORD_LETTERS.extend( [' ', '\t', '\n', '\r', '\f', '\v', '\b'] )

    def format( self, field_with_format ):
        #check if it is the format:$name;format="Camel"$
        tmp = field_with_format.split(";")
        if len(tmp) == 2 and tmp[1].startswith( "format="):
            formats = tmp[1][len("format=")+1:-1].split(',')
            value = self._fields_value[ tmp[0] ]
            for f in formats:
                value = self._format_with_name( value, f )
            return value
        else: #check if it is in format: $organization__packaged$
            pos = field_with_format.rfind("__")
            if pos != -1:
                value = self._fields_value[ field_with_format[0:pos] ]
                f = field_with_format[pos+2:]
                return self._format_with_name( value, f )

            #no format info, return the value
            return self._fields_value[field_with_format]
            

    def _format_with_name( self, value, format_name):
        if format_name in self._format_methods:
            return self._format_methods[format_name](value)
        else:
            return value
    def _upper( self, value ):
        return value.upper()

    def _lower( self, value ):
        return value.lower()

    def _capitalize( self, value ):
        return "%s%s"%(value[0].upper(), value[1:])

    def _decapitalize( self, value ):
        return "%s%s" %(value[0].lower(), value[1:])

    def _startCase( self, value ):
        words = map( lambda w: self._capitalize(w), value.split() )
        return "".join(words)

    def _word(self,value):
        return "".join( map( lambda c: c if c in self.WORD_LETTERS else '', value ) )

    def _upperCamel( self, value ):
        return self._word( self._startCase( value ) )

    def _lowerCamel( self, value ):
        return self._word( self._startCase( self._decapitalize( value ) ) )

    def _hyphen( self, value ):
        return "".join( map( lambda c: '-' if c.isspace() else c, value ) )

    def _normalize( self, value ):
        return self._lower( self._hyphen( value ) )

    def _snake( self, value ):
        return "".join( map( lambda c: '_' if c.isspace() or c =='.' else c, value ) )

    def _packaged(self, value):
        return "".join( map( lambda c: '/' if c == '.' else c, value ) )

    def _random( self, value ):
        random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        return "%s%s" %(value, random_str)


def load_properties( fileName ):
    props = {}
    with open(fileName) as fp:
        for line in fp:
            line = line.strip()
            if len( line ) <= 0 or line[0] == '#':
                continue
            pos = line.find( '=' )
            if pos != -1:
                props[ line[0:pos].strip() ] = line[pos+1:].strip()

    for prop in props:
        props[prop] = replace_fields( props[prop], props )
    return props

def replace_fields( s, props ):
    start = s.find('$' )
    if start == -1:
        return s

    result = s[0:start]
    tmp_field = TempField(props)
    while True:
        end = s.find( '$', start + 1 )
        if end == -1:
            return "%s%s"%(result,s[start+1:])
        else:
            result = "%s%s" % (result, tmp_field.format(s[start+1:end]) )
            start = s.find( '$', end + 1 )
            if start == -1:
                return "%s%s" % (result, s[end+1:] )
            else:
                result = "%s%s" %(result,s[end+1:start] )

def prompt_user_change_fields( props ):
    for prop in props:
        s = raw_input( "Your %s(%s):" % (prop, props[prop]) ).strip()
        if len( s ) != 0:
            props[prop] = s

def list_files( root_dir ):
    result = []
    if os.path.isdir( root_dir ):
        files = os.listdir(root_dir)
        for f in files:
            full_name = os.path.join( root_dir, f )
            if os.path.isdir( full_name ):
                result.extend( list_files( full_name ) )
            else:
                result.append( full_name )
    else:
        result.append( root_dir )

    return result

def get_project_file_name( template_root_dir, project_name, file_name ):
    temp_root_dirs = filter( lambda x: len( x ) > 0, template_root_dir.split( os.sep ) )
    file_names = filter( lambda x: len( x ) > 0, file_name.split( os.sep ) )

    if len( file_names ) > len( temp_root_dirs ) and file_names[0:len( temp_root_dirs)] == temp_root_dirs:
        t = [project_name]
        t.extend( file_names[len( temp_root_dirs):] )
        return os.path.join( *t )
    else:
        return file_name


def create_dir_of( file_name ):
    dir_name = os.path.dirname( file_name )
    if not os.path.exists( dir_name ):
        os.makedirs( dir_name )
def write_file( file_name, content ):
    with open( file_name, "wt" ) as fp:
        fp.write( content )

def is_text_file( fileName ):
    TEXT_SUFFIX = [".java", ".scala", ".sbt", ".properties", ".txt", ".text"]
    for suffix in TEXT_SUFFIX:
        if fileName.endswith( suffix ):
            return True
    return False

def clone_template( git_url ):
    tmp = git_url.split( "/" )
    if len( tmp ) == 2:
        git_url = "https://github.com/%s" % git_url
        if not git_url.endswith( ".git" ):
            git_url = "%s.git" % git_url

    os.system( "git clone %s" % git_url )
    return git_url.split("/")[-1][0:-4]

def main( g8_temp_root ):
    if g8_temp_root.endswith( ".git" ) or g8_temp_root.endswith(".g8"):
        g8_temp_root = clone_template( g8_temp_root )
    root_dir = os.path.join( g8_temp_root, 'src/main/g8')
    files = list_files(root_dir)
    props = load_properties( os.path.join( root_dir, 'default.properties') )
    project = raw_input( "Your project:" ).strip()
    prompt_user_change_fields(props)
    for fileName in files:
        realFileName = replace_fields( fileName, props )
        dest_file = get_project_file_name( root_dir, project, realFileName )
        create_dir_of( dest_file )
        if is_text_file( fileName ): 
            with open(fileName) as fp:
                content = fp.read()
                content = replace_fields( content, props )
                write_file( dest_file, content )
        else:
            shutil.copyfile( fileName, dest_file )


if __name__ == "__main__":
    if len( sys.argv ) < 2:
        print( "Usage: giter8.py <giter8_template_directory>")
        sys.exit(1)
    else:
        main( sys.argv[1] )

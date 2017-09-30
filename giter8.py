#!/usr/bin/python

import os
import os.path
import random
import requests
import shutil
import sys
import xml.etree.ElementTree as ET 

class TempField:
    """
    the template field in the giter8
    """
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

class Properties:
    def __init__( self, fileName ):
        self._fileName = fileName
        self._props = {}
        self._propOrder = []
        self._load()
        self._temp_fields = TempField( self._props )

    def change_prop_with_prompt( self ):
        """
        change property value with prompt
        """
        for prop in self._propOrder:
            value = self._props[prop]
            maven_prop = self._parse_as_maven_prop( value )
            if maven_prop is not None:
                value = get_version_from_maven( maven_prop[0], maven_prop[1], maven_prop[2] )    
            else:
                value = self.replace_fields( self._props[prop] )
            self._props[prop] = value
            value = raw_input( "%s(%s):" % (prop,value) ).strip()
            if len( value ) > 0:
                self._props[prop] = value

    def _parse_as_maven_prop( self, value ):
        """
        first check if the value is in format:maven(groupId, artifactId ) or
        maven( groupId, artifactId, stable). If it is in one of above, a tuple
        with three elements are returned

        Args:
            value: the value to check

        Return:
            None if the format not match maven(groupId, artifactId ) or maven( groupId, artifactId, stable)
            tuple with three elements (groupId, artifactId, stable). stable is a boolean: true indicates
            a stable release, false indicates any latest release
        """
        # check if the value is in format: maven(groupId, artifactId ) or maven( groupId, artifactId, stable)
        if not value.startswith( "maven" ):
            return None
        value = value[len("maven"):].strip()

        if not value.startswith( "(" ) or not value.endswith( ")" ):
            return None

        value = value[1:-1]
        value = value.split(",")
        # strip the split word and discard the empty words
        value = map( lambda x: x.strip(), value )
        value = filter( lambda x: len( x ) > 0, value )
        if len(value) == 2 or len(value) == 3:
            return (value[0], value[1], False if len( value ) == 2 else value[2] == 'stable' )
        else:
            return None


    def _load( self ):
        with open( self._fileName ) as fp:
            for line in fp:
                line = line.strip()
                if len( line ) <= 0 or line[0] == '#':
                    continue
                pos = line.find('=')
                if pos != -1:
                    prop = line[0:pos].strip()
                    value = line[pos+1:].strip()
                    self._props[prop] = value
                    self._propOrder.append( prop )

    def get_field( self, name ):
        """
        get the value of a field
        """

        return self.replace_fields( "" if name not in self._props else self._props[name])
    
    def get_file_name_with_template( self, file_name_template):
        PACKAGE_VAR = '$package$'
        start_pos = 0
        package_pos = file_name_template.find( PACKAGE_VAR, start_pos )
        result = ""
        while package_pos != -1:
            result = "%s%s%s" % (result, file_name_template[start_pos:package_pos], self.get_field( "package" ).replace('.', '/') )
            start_pos = package_pos + len( PACKAGE_VAR )
            package_pos = file_name_template.find( PACKAGE_VAR, start_pos )
        return self.replace_fields("%s%s" % (result, file_name_template[start_pos:]))

    def replace_fields(self, value ):
        """
        find all fields( between two "$") and replace the fields
        with the values in this properties

        Args:
            value: a value possible includes the fields

        Returns: all the fields replaced by the value in this properties
        """

        # find the start flag '$'
        start = 0
        result = ""
        cond_express_start_pos = -1
        cond_express_level = 0
        while True:
            field_info = self._find_field( value, start )

            if field_info is None:
                return "%s%s" % ( result, value[start:] )
            else:
                (field_start_pos, field_end_pos, field_name ) = field_info
                if self._is_start_cond_expression( field_name ):
                    cond_express_level += 1
                    cond_express_start_pos = start
                elif self._is_end_cond_expression( field_name ):
                    cond_express_level -= 1
                    if cond_express_level == 0:
                        result = "%s%s" % (result, self._replace_fields_with_condition( value[cond_express_start_pos: field_end_pos + 1 ] ) )
                        cond_express_start_pos = -1
                elif cond_express_start_pos == -1:
                    result = "%s%s" % (result, value[start:field_start_pos])
                    result = "%s%s" % (result, self._temp_fields.format(field_name) )
                start = field_end_pos + 1

    def _find_field( self, value, start_pos ):
        """
        find a field start and end with flag '$'

        Args:
            value: the value may contains field start&end with flag '$'
            start_pos: the start search position
        Returns:
            None if no field in the value
            a tuple with three elements (field_start_pos, field_end_pos, field_name) if a field is found
        """
        field_start_pos = value.find( '$', start_pos )
        if field_start_pos == -1:
            return None
        field_end_pos = value.find( '$', field_start_pos + 1 )
        if field_end_pos == -1:
            return None

        return (field_start_pos, field_end_pos, value[field_start_pos + 1: field_end_pos] )

    def _is_start_cond_expression( self, value ):
        """
        check if a conditional express is started. A start conditional express is
        start like: if(var.truthy)

        Args:
            the value to be checked

        Return:
            True if the value is started like: if(var.truthy)
        """
        cond_exp = self._parse_cond_expression( value )
        return cond_exp is not None and cond_exp[0] == 'if'

    def _parse_cond_expression( self, value ):
        if value.startswith( "if" ) or value.startswith( "elseif" ):
            start = value.find( '(' )
            end = value.find( ')' )
            if start != -1 and end != -1:
                return ( "if" if value.startswith( "if" ) else "elseif", value[start+1:end].strip() )
        elif value.startswith( "else" ):
            return ("else", "unused")
        elif value.startswith( "endif" ):
            return ("endif", "unused")

        return None

    def _is_end_cond_expression( self, value ):
        """
        check if the value is conditional end flag: endif

        Args:
            the value to be checked
        Return:
            true if the value is "endif" string
        """
        return value == "endif"
    def _replace_fields_with_condition( self, value ):
        start = 0

        cond_exp = ConditionalExpression( self )
        statement = ""

        while True:
            field_info = self._find_field( value, start )
            if field_info is None:
                break

            (field_start_pos, field_end_pos, field_name) = field_info
            cond_exp_info = self._parse_cond_expression( field_name )
            if cond_exp_info is None:
                statement = "%s%s" % (statement, value[start:field_end_pos+1] )
            else:
                statement = "%s%s" % (statement, value[start:field_start_pos ] )
                if len(statement) > 0:
                    cond_exp.add_statement( statement )
                    statement = ""
                if cond_exp_info[0] == 'if':
                    cond_exp.if_exp( cond_exp_info[1] )
                elif cond_exp_info[0] == 'elseif':
                    cond_exp.elif_exp( cond_exp_info[1] )
                elif cond_exp_info[0] == 'else':
                    cond_exp.else_exp()
                elif cond_exp_info[0] == 'endif':
                    return cond_exp.evaluate()

                start = field_info[1] + 1
        return value

class ConditionalExpression:
    def __init__( self, props ):
        self._if_exp = None
        self._if_statements = []
        self._elif_exps = []
        self._elif_statements=[]
        self._else_statements=[]
        self._props = props
        self._cur_statements = None

    def add_statement( self, statement ):
        if self._cur_statements is not None:
            self._cur_statements.append( statement )

    def if_exp( self, expression ):
        self._if_exp = expression
        self._cur_statements = self._if_statements

    def elif_exp( self, expression ):
        self._elif_exps.append( expression )
        self._cur_statements = self._elif_statements

    def else_exp( self ):
        self._cur_statements = self._else_statements

    def evaluate( self ):
        if self._is_true( self._if_exp ):
            return self._props.replace_fields( "".join( self._if_statements ) )
        index = 0
        for elif_exp in self._elif_exps:
            if self._is_true(  elif_exp ):
                return self._props.replace_fields(self._elif_statements[index])
            index += 1

        return self._props.replace_fields( "".join( self._else_statements ) )

    def _is_true( self, value ):
        return value.endswith( '.truthy' ) and self._props.get_field(value[:-1*len('.truthy')]) in ['y', 'yes', 'true']

def get_version_from_maven( groupId, artifactId, stable = False ):
    r = requests.get( "http://repo1.maven.org/maven2/%s/%s/maven-metadata.xml" % ( groupId.replace('.', '/'), artifactId) )
    if r.status_code >= 200 and r.status_code < 300:
        root = ET.fromstring( r.text )
        versioning = root.find('versioning')
        if stable:
            return versioning.find( 'release' ).text
        else:
            return versioning.find( 'latest' ).text
    return ""

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
    TEXT_SUFFIX = [".java", ".scala", ".sbt", ".properties", ".txt", ".text", ".htm", ".html"]
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
    props = Properties( os.path.join( root_dir, 'default.properties') )
    project = raw_input( "Your project:" ).strip()
    props.change_prop_with_prompt()
    for fileName in files:
        
        realFileName = props.get_file_name_with_template( fileName )
        dest_file = get_project_file_name( root_dir, project, realFileName )
        create_dir_of( dest_file )
        if is_text_file( fileName ): 
            with open(fileName) as fp:
                content = fp.read()
                content = props.replace_fields( content )
                write_file( dest_file, content )
        else:
            shutil.copyfile( fileName, dest_file )


if __name__ == "__main__":
    if len( sys.argv ) < 2:
        print( "Usage: giter8.py <giter8_template_directory>")
        sys.exit(1)
    else:
        main( sys.argv[1] )

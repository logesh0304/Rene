# The MIT License
#
# Copyright 2020 Logesh0304.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import collections
import os
import re
import sys
import typing
import pathlib
from pathlib import Path
import glob
from typing import *

_version='v1.1.0'
_help="""
  usage: rene [-glob] [ -f | -d | -a ]  [[-base] <basedir>] [-pat] <pattern> [-templt] <template> 
            [-max <number>] [-r] [ -bf | -df ] [-p]
            [-h] [-v]

    -glob      - match files using 'glob' instead of 'regex' 

            Note: You sould use glob-pattern (not regex-pattern) if this option is enabled.
                  Group replacement is not supported in glob, you have to use 'attributes'

    -f         - files only (default)
    -d         - directory only
    -a         - any
    
    <basedir>  - base directory for searching files (current directory is default)
    <pattern>  - regex or glob pattern for searching file (use '/' as path seperator)
    <template> - template string for renaming matched files

            Note: you can also use -base, -pat and -templt to specify the base directory, pattern and template.
                  This has use only in the case where the matching pattern is same as any of arguments.

    -max       - maximum number of files to be renamed (-1 is default)
    -r         - enables recursive-search-mode. This is used when you want to match files in subdirectories also

            Note: use [^/] instead of . (matches path-seperator '/' also) in regex to match only names if recursive-search-mode is enabled

    -bf        - search files in breadth-first manner
    -df        - search files in depth-first manner
    
            Note: The above two works only when recursive-search-mode is enabled and it is only for regex.
                  Using -r, -bf, -df has no effect in glob (always do recursive search)

    -p         - rename the file's path from base directory (only for recursive-search-mode).
                
    -h shows this help
    -v shows version of this script
    -i enter into interactive mode

  This is a open-source project, contribute to this project if you like.
  For more details visit this project's github page, https://github.com/logesh0304/Rene
"""

class ListIncrementor:
    def __init__(self, base: List, initial: List=None, step: int=1):
        if not base :
            raise ValueError('base list cannot be empty')
        self.base=base
        self.step=step
        if step<0:  
            raise ValueError(f"'step'({step}) cannot be neagative")
        self.initial= [base[0]] if initial is None else initial
        self.current= self.initial
        self.first_el, self.last_el =base[0], base[len(base)-1]

    def incr_by_conf(self, lst: List, step=None, idx=None):
        if step is None :   # if step is none, uses default step
            step=self.step
        elif step<0:  
            raise ValueError(f"'step'({step}) cannot be neagative")
        
        if idx is None :    # if idx is none, uses last idx 
            idx = len(lst)-1
        # if incremented index is not larger than length of base, assign it
        if (inc_idx:=(self.base.index(lst[idx])+step)) < len(self.base) :
            lst[idx]=self.base[inc_idx]
        # else increment element before idx 
        else:   
            # getting quotien
            # t and remainder
            # remainder, quotient is for inementing element in idx, before idx
            # by considering "current place is incremented by total length of base, the place before current is incremented by 1 and the recurtion follows"
            q,r=divmod(inc_idx, len(self.base))
            lst[idx]=self.base[r]
            # incremeting  element before idx
            if idx>0 :
                self.incr_by_conf(lst, q, idx-1)
            else:   # if there is no element before idx, add an element
                lst.insert(0, self.base[0])
                # if remaining step is more than 1, increment the new element
                if stp:=q-1 != 0 :
                    self.incr_by_conf(lst, stp, 0)
    
    def incr(self, step=None):
        to_return=self.current.copy()
        self.incr_by_conf(self.current, step)
        return to_return

    def reset(self):
        self.current=self.initial

class Incrementor:

    NUM='num'; ALPHA='alpha'; ALNUM='alnum'
    
    # args :
    #   num     - initial, width=0, step
    #   alpha   - initial, [case > up, lw, lu], step
    #   alpha   - initial, intWidth=None, case, step , intMaxCount

    def __init__(self, incrType, arg_str):
        args, kwargs = Incrementor.__parse_args(arg_str)
        try :
            if incrType == Incrementor.NUM :
                self.incr_obj = Incrementor.NumIncrementor(*args, **kwargs)
            elif incrType == Incrementor.ALPHA :
                self.incr_obj = Incrementor.AlphaIncrementor(*args, **kwargs)
            elif incrType == Incrementor.ALNUM :
                self.incr_obj = Incrementor.AlnumIncrementor(*args, **kwargs)
            else :
                raise ValueError(f'There is no incrementor type like \'{incrType}\'')
        except TypeError as te:
            show_error(f'Invalid arguments passed to {incrType.capitalize()}Incrementor')

    def incr(self):
        return self.incr_obj.incr()
        

    @staticmethod
    # Parse args for iters and return args and kwargs as a list and dict
    # we can mix positional and keywords args, but positional args are taken first
    def __parse_args(arg_str: str):
        args=[]
        kwargs={}
        if arg_str :
            arg_list=re.split(r'\s+', arg_str)
            for arg in arg_list :
                if arg: # only if arg is not empty
                    if (idx:=arg.find('='))!=-1 :
                        kwargs[arg[:idx]] = arg[idx+1:]
                    else:
                        args.append(arg)
        return args, kwargs

    class NumIncrementor:
        # args can be int or string representation of int
        def __init__ (self, init=0, step=1, width=None):
            try :
                self.current = int(init)
                # width is calculated using init (i.e. 0001 is taken as same as 0001 not 1)
                self.min_width= int(width) if width is not None else len(init) if type(init) is str else 0
                self.incr_step=int(step)
            except ValueError:
                show_error('Invalid arguments to NumIncrementor')
            if self.min_width<0 :
                show_error('Width cannot be negative')

        def incr (self, step=None) :
            # using zfill instead of rjust. so, minus sign is always in first
            to_return = str(self.current).zfill(self.min_width)
            incr_step = self.incr_step if step is None else step
            self.current += incr_step
            return to_return

    class AlphaIncrementor:
        alpha_upper = [ chr(i) for i in range(65,91) ]
        alpha_lower = [ chr(i) for i in range(97, 123) ]
        alpha_all = alpha_upper + alpha_lower

        def __init__ (self, init: str='A', step=1, case: Optional[str]=None) :
            # if case is None, the case of initial is used
            if case == None :
                if init.isupper() :
                    alpha = Incrementor.AlphaIncrementor.alpha_upper
                elif init.islower() :
                    alpha = Incrementor.AlphaIncrementor.alpha_lower
                else :
                    alpha = Incrementor.AlphaIncrementor.alpha_all
            # if case is specified, case of the initial is changed according to the specifed case 
            elif case == 'up' :
                alpha = Incrementor.AlphaIncrementor.alpha_upper
                init = init.upper()
            elif case == "lw" :
                alpha = Incrementor.AlphaIncrementor.alpha_lower
                init = init.lower()
            elif case == 'ul' :
                alpha = Incrementor.AlphaIncrementor.alpha_all
            else :
                show_error(f'\'{case}\' is not an keyword for case')
            
            if not init.isalpha():
                show_error(f'{init} is not alphabetic')
            try:
                self.iter=ListIncrementor(alpha ,list(init), int(step))
            except ValueError as ve:
                if str(ve).startswith('invalid literal'):
                    show_error('Invalid arguments passed to AlphaIncrementor')
                else:
                    show_error(ve)
            self.current=self.iter.current 

        def incr(self, step=None) :
            return ''.join(self.iter.incr(step))
    
    class AlnumIncrementor:
        
        def __init__ (self, init='A0', step=1, case=None, intWidth=None, intMaxCount=None):
            try:
                self.incr_step = int(step)
                if self.incr_step < 0 :
                    show_error(f"'step'({step}) cannot be negative")
                # seperate alphabet and integer part
                temp_ = re.split(r'(?<=[A-Za-z])(?=\d)', init)
                if len(temp_)!=2:
                    show_error(f'{init} is not a valid initial value for AlnumIncrementor')
                # current uses AlphaIncrementor for alphabet part
                self.current  = [Incrementor.AlphaIncrementor(temp_[0], case=case), 
                                    int(temp_[1])]
                # intWidth is calculated using init, if it is not given (i.e. 0001 is taken as same as 0001 not 1)
                self.int_min_width = len(temp_[1]) if intWidth is None else int(intWidth)
                # if max count is None, it is calculated based on width
                self.int_max_count = int('1'+('0'*self.int_min_width)) if not intMaxCount else int(intMaxCount)
            except ValueError : 
                show_error("Invalid arguments passed to AlnumIncrementor")

            if self.int_min_width<0 :
                show_error('Width cannot be negative')

        def incr(self, step=None):
            to_return = ''.join(self.current[0].current)+str(self.current[1]).rjust(self.int_min_width, '0')

            incr_step = self.incr_step if step is None else step
            # increment integer part,
            # if integer part is greater than max count, increment alpha part
            if (n_val := self.current[1]+incr_step) < self.int_max_count-1 :
                self.current[1]=n_val
            else :
                q,r = divmod(n_val, self.int_max_count)
                self.current[0].incr(q)
                self.current[1] = r
            return to_return

# attributes common for all files
static_attribs={
    'base'   :'',
    'base_parent' :''
}

incrs: Dict[int, Incrementor]={}

def sub_attrib(templt: str, attribs: Dict[str, str]={}):
    final_str=''
    last_pos=0  # end position of last match
    # iterating the group(1) of founded matches
    for i, match in enumerate(re.finditer('<:(.+?):>', templt)):
        group = match.group(1)
        attrib, arg= group.split(' ', 1) if ' ' in group else (group, '')
        attrib_val=''
        # check if the attribute is an incrementor
        if attrib in (Incrementor.NUM, Incrementor.ALPHA, Incrementor.ALNUM) :
            if i not in incrs :
                incrs[i]=Incrementor(attrib, arg)
            attrib_val=incrs[i].incr()
        else:
            try:
                attrib_val = attribs[attrib] if attrib in attribs else static_attribs[attrib]
            except KeyError as ke:
                show_error(f'There is no attribute like "{attrib}", please use the correct attribute')
        # replace attribute with its value
        final_str+=templt[last_pos:match.start()] + attrib_val
        last_pos=match.end()
    # append unmatched remaining string to final_str
    if last_pos != len(templt):
        final_str+=templt[last_pos:]

    return final_str

def show_error(err, header='Error', exit_=True, confirm_before_exit=False, confirm_msg='Would you like to continue ?',exit_msg='', inverse_yn=False):
    if err :
        print(header+': 'if header else '', err, sep='', file=sys.stderr)
    if exit_:
        if confirm_before_exit :
            positive, negative = ('y', 'n') if not inverse_yn else ('n', 'y')
            # ask the question until you answer yes(y) or no(n) 
            while True :
                a=input(confirm_msg+' (y/n) :').lower()
                if a == 'y' :
                    break
                elif a == 'n':
                    sys.exit(exit_msg)
        else :
            sys.exit(exit_msg)
    
# rename file with new name specified in name map.
# if sort is True, it sorts the path of the files (files in deepest subdirectory has more priority)
def rename(name_map, sort=False): 
    if name_map :
        n=0
        print("Preview:")
        for item, new_name in name_map.items() :
                print('\t'+str(item.relative_to(base_path))+'\t->\t'+str(new_name.relative_to(base_path)))
        show_error('', confirm_before_exit=True, confirm_msg='Confirm to rename', exit_msg='Rename cancelled !!')
        if sort:
            # sorting the paths by depth, for renameming the files in the subdirectories first
            name_list=list(name_map.items())
            name_list.sort(key = lambda x : str(x[0]).count('\\'), reverse=True)
            name_map=dict(name_list)
        for item, new_name in name_map.items() :
            try:
                item.rename(new_name)
                n+=1    # increment n when rename is success
            except FileExistsError as fee:
                show_error(f'File name already exixts, cannot rename : {fee.filename} -> {fee.filename2}',
                    header="Warning",
                    confirm_before_exit=True,
                    confirm_msg='would you like to skip this file ?'
                )
            except OSError as oe:
                show_error(oe)
        return n
    else :
        print('No files matched the pattern !!')
        return None
        
# returns the new-name of the given file based on the given template
def get_newname(path: Path, templt, rename_path=False):
    attribs={}
    attribs['name']=path.stem
    attribs['full_name']=path.name
    attribs['ext']=path.suffix[1:] if path.is_file() else ''
    attribs['parent']=path.parent.name
    # path of file(parent) relative to base-path
    attribs['path']='' if (_:=str(path.parent.relative_to(base_path).as_posix())) == '.' else _+'/' 
    attribs['abs_path']=str(path.parent.resolve().as_posix())+'/'
    new_name=sub_attrib(templt, attribs)
    # if from_base is True, path is not appended to new name (for also renaming the path) 
    # and templt should specifies the new path of the file
    return new_name if rename_path else attribs['path']+new_name

# search the files is current directory using regex pattern
def search(pat, templt, filedir='f', max_files=-1):
    name_map={} # dict containg oldname (name means path of the file) and newname
    matched=0
    for item in base_path.iterdir(): 
        # check whether to rename a file or dir or both
        if matched!=max_files and ((filedir=='a') or (filedir=='f' and item.is_file()) or (filedir=='d' and item.is_dir())) and (group:=re.fullmatch(pat, item.name)) != None:
            name_map[item]=base_path.joinpath(group.expand(get_newname(item, templt)))
            matched+=1
    return name_map

# search the files recursively (i.e. also in subdirectory) using regex pattern 
# form_base specifies whether to rename only name of the file (false)(default) or entire path of the file from base_directory (true)
def recr_search(pat, templt, filedir='f', max_files=-1, s_type='bf', rename_path=False):
    name_map={}
    matched = 0 
    if s_type not in ['bf', 'df'] :
        raise ValueError(f"{s_type} is not 'bf' or 'df'") 
    for dir_path, dirs, files in os.walk(base_path, topdown=True if s_type=='bf' else False) :
        p_list=files if filedir=='f' else (dirs if filedir=='d' else files+dirs)
        for item in p_list : 
            path=Path(os.path.join(dir_path, item))
            # posix-path is used (which uses / insdead if \)due to \ are used in regex replacement patterns
            posixpath=path.relative_to(base_path).as_posix()
            if matched!=max_files and (match:=re.fullmatch(pat, posixpath)) != None:
                name_map[path]=base_path.joinpath(match.expand(get_newname(path, templt, rename_path)))
                matched+=1
    return name_map

# search the files using glob pattern
def glob_search(pat, templt, filedir='f', max_files=-1, rename_path=False):
    name_map={}
    matched = 0
    for item in glob.iglob(str(base_path)+'\\'+pat, recursive=True) :
        path = Path(item)
        if matched!=max_files and ((filedir=='a') or (filedir=='f' and path.is_file()) or (filedir=='d' and path.is_dir())) :
            name_map[path]=base_path.joinpath(get_newname(path, templt, rename_path))
            matched+=1
    return name_map       

# default values for command line arguments
arg_def_val={
        'base' : '',
        'filedir' : 'f',
        'pat' : None,
        'templt' : None,
        'max' : -1,
        'glob' : False,
        'recr' : False,
        'rs_type' : 'bf', # recursive search type : breath-first or depth-first
        'rn_path' : False
}

def parse_args() :
    args=collections.deque(sys.argv[1:])
    argval=arg_def_val.copy()
    unknown=[]

    try:
        while(args):
                arg=args.popleft()
                if arg == '-h' :     sys.exit(_help)
                elif arg == '-v' :   sys.exit(_version)
                elif arg == '-i' :   return interact()
                elif arg == '-glob'            : argval['glob']=True
                elif arg == '-base'            : argval['base']=args.popleft()
                elif arg in ['-f', '-d', '-a'] : argval['filedir']=arg[1:]
                elif arg == '-pat'             : argval['pat']=args.popleft()
                elif arg == '-templt'          : argval['templt']=args.popleft()
                elif arg == '-max'             : argval['max']=int(args.popleft())
                elif arg == '-r'               : argval['recr']=True
                elif arg in ['-bf', '-df']     : argval['rs_type']=arg[1:]
                elif arg == '-p'               : argval['rn_path']=True
                else: # positional arguments
                    unknown.insert(0, arg)

    except IndexError or ValueError :
        sys.exit('Given arguments are invalid !!\n'+_help)

    # pat and templt has priority over base
    for val in unknown:
        if not argval['templt']  : argval['templt']=val
        elif not argval['pat']  : argval['pat']=val
        elif not argval['base'] : argval['base']=val
        else:
            sys.exit('Given arguments are invalid !!\n'+_help)

    if not (argval['pat'] and argval['templt']):
        sys.exit('Given arguments are invalid !!\n'+_help)
    return argval

def interact():
    print('Rene - Interactive Mode')
    argval=arg_def_val.copy()

    # help, exit
    res=input("press Enter to continue or type 'help' to display help and 'quit' to exit\n")
    if res=='help' :
        print(_help)
        return interact()
    elif res=='quit' :
        sys.exit()
    print('Enter nothing for default values')

    # base
    if base:=input('> Base-directory (current directory is default) :') : argval['base']=base
    # else, it use default value in argval

    # is_glob
    if input('> [r]egex (default) or [g]lob (r/g) :') == 'g' : argval['glob']=True

    # pat
    while not (pat:=input('> Pattern :')):
        print('This cannot be empty !!')
    argval['pat']=pat

    # templt
    while not (templt:=input('> Template :')):
        print('This cannot be empty !!')
    argval['templt']=templt

    # file-dir
    if (tmp_fd:=input('Rename only,\n\t1. [f]iles (default)\n\t2. [d]irectory\n\t3. [a]ny\n> Enter (f/d/a) :')) in ('f','d','a') :
        argval['filedir']=tmp_fd
    
    # max
    while True :
        try:
            if max_:=input('> Maximum files (-1 (default) means no limit) :') :
                argval['max']=int(max_)
            break
        except ValueError:
            print('Value should be an integer !!')

    # recr
    if input('> Enable recursive-search-mode (y/n default) :') == 'y' : argval['recr']=True

    # s_type
    if input('> Recursive search type,\n\t[b]readth-first (default) or [d]epth-first (b/d) :') == 'd' : argval['rs_type']='df'

    # from_base
    if input('> Rename path of file (y/n default) :') == 'y' : argval['rn_path']=True
    print() # prints empty line
    return argval

base_path=Path('')
def main():
    argval = parse_args() if len(sys.argv)>1 else interact()
    global base_path
    base_path = Path(argval['base'])
    if base_path.absolute() == Path(__file__).parent :
        show_error('You are trying to rename the files in the folder where this program is running',
            header='Warning',
            confirm_before_exit=True,
            confirm_msg='Are you sure about renaming the files ?',
        )
    # assigning static attributes
    static_attribs['base']=argval['base']
    static_attribs['base_parent']= base_path.parent.name
    try:
        if argval['glob'] :
            name_map=glob_search(argval['pat'], argval['templt'], argval['filedir'], argval['max'], argval['rn_path'])
            n=rename(name_map, True)
        else:
            if argval['recr'] :
                name_map=recr_search(argval['pat'], argval['templt'], argval['filedir'], argval['max'], argval['rs_type'], argval['rn_path'])
                n=rename(name_map, True)
            else :
                name_map=search(argval['pat'], argval['templt'], argval['filedir'], argval['max'])
                n=rename(name_map)
        if not n is None:
            print('Files matched:',len(name_map))
            print('Files renamed:',n)
        
    except FileNotFoundError as fnfe:
        show_error(fnfe)
    except re.error as rerr:
        show_error(rerr, header='PatternError')    
    except Exception as e:
        raise e
        sys.exit('Sorry, an error occured !!')
    input('press Enter to exit...')
    

if __name__ == "__main__":
    main()
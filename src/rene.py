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

import sys
import collections
import os
import re
from typing import *
import typing
from pathlib import Path
import array

_version='1.0.0'
_help="""usage: rene [ -f | -d | -a ]  [ [-base] <basedir>] [-pat] <pattern> [-templt] <template> [-max <number>]

  -f         - files only
  -d         - directory only
  -a         - any 
  (-f is default)

  <basedir>  - base directory for searching files 
                (if it is not given, current directory will be used)
  <pattern>  - regular expression pattern for searching file
  <template> - template string for renaming matched files

  ** you can also use -pat and -templt to specify the pattern and template.
     This has use only in the case where the file name is same as any of arguments.

  -max       - maximum number of files to be renamed

  -h shows this help
"""

_filedir={'-a' : 0, '-f' : 1, '-d' : 2}

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
            # remainder, quotient is for incrementing element in idx, before idx
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
        except TypeError:
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
        def __init__ (self, init=0, step=1, width=0):
            try :
                self.current = int(init)
                self.min_width=int(width)
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

        def __init__ (self, init: str='A', step=1, case: Optional[str]=None,) :
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
        
        def __init__ (self, init='A0', step=1, case=None, intWidth=1, intMaxCount=None):
            try:
                self.incr_step = int(step)
                if self.incr_step < 0 :
                    show_error(f"'step'({step}) cannot be negative")
                # seperate alphabet and integer part
                temp_ = re.split(r'(?<=[A-Za-z])(?=\d)', init)
                if len(temp_)!=2:
                    show_error(f'{init} is not a valid initial value for AlnumIncrementor')
                # current uses AlphaIncrementor for alphabet part
                self.current  = [Incrementor.AlphaIncrementor(temp_[0], case), 
                                    int(temp_[1])]
                self.int_min_width = int(intWidth)
                # if max count is None, it is calculated based on width
                self.int_max_count = int('1'+('0'*self.int_min_width)) if not intMaxCount else int(intMaxCount)
            except ValueError : 
                show_error("Invalid arguments passed to AlnumIncrementor")

            if self.min_width<0 :
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

static_attribs={
    'base_dir'  :'test',
    'parent'    :''
}

incrs: Dict[int, Incrementor]={}

def sub_attrib(file_pat: str, attribs: Dict[str, str]={}):
    final_str=''
    last_pos=0  # end position of last match
    # iterating the group(1) of founded matches
    for i, match in enumerate(re.finditer('<:(.+?):>', file_pat)):
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
        final_str+=file_pat[last_pos:match.start()] + attrib_val
        last_pos=match.end()
    # append unmatched remaining string to final_str
    if last_pos != len(file_pat):
        final_str+=file_pat[last_pos:]

    return final_str

# prints the error message without stacktrace
#  exit_ -> to exit after printing error message
#  conform_before_exit -> if true ask user to exit or not. This has no effect if "exit_" is false
def show_error(err, header='Error', exit_=True, confirm_before_exit=False, confirm_msg='Would you like to continue ?'):
    print(header+': 'if header else '', err, sep='', file=sys.stderr)
    if exit_:
        if confirm_before_exit :
            # ask the question until you answer yes(y) or no(n) 
            while True :
                a=input(confirm_msg+' (y/n) :').lower()
                if a == 'n' :
                    sys.exit()
                elif a == 'y':
                    break
        else :
            sys.exit()
    
def rename(name_map): 
    n=0
    for item, new_name in name_map.items() :
        try:
            item.rename(new_name)
            print('\t'+item.name+'\t->\t'+new_name.name)
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
        
def rene(base_path: Path, pat, templt, filedir=1, max_files=-1):
    name_map={}
    attribs={}
    try:
        i=0
        for item in base_path.iterdir():
            # check whether to rename a file or dir or both
            if i!=max_files and ((filedir==0) or (filedir==1 and item.is_file()) or (filedir==2 and item.is_dir())) and (group:=re.fullmatch(pat, item.name)) != None:
                # adding attributes
                attribs["name"]=item.stem
                if item.is_file() :
                    attribs["full_name"]=item.name
                    attribs["ext"]=item.suffix[1:]
                new_name=sub_attrib(templt, attribs)  # sustituting attributes
                name_map[item]=base_path.joinpath(group.expand(new_name))
                i+=1
    except FileNotFoundError as fnfe:
        show_error(fnfe)
    except re.error as rerr:
        show_error(rerr, header='PatternError')

    n=rename(name_map)
    print('Files matched:',len(name_map))
    print('Files renamed:',n)

def parse_args():
    args=collections.deque(sys.argv[1:])
    filedir=1
    max_files=-1
    bpt=[]
    base_dir=pat=templt = ''

    try:
        while(args):
                arg=args.popleft()
                if arg == '-h' : sys.exit(_help)
                elif arg in _filedir : filedir=_filedir[arg]
                elif arg == '-max' : max_files=int(args.popleft())
                elif arg == '-base' : base_dir=args.popleft()
                elif arg == '-pat' : pat=args.popleft()
                elif arg == '-templt' : templt=args.popleft()
                else:
                    bpt.insert(0, arg)
    except IndexError or ValueError:
        sys.exit('Invalid arguments given !!')

    for i in bpt:
        if not templt:
            templt=i
        elif not pat:
            pat=i
        elif not base_dir:
            base_dir=i
        else:
            sys.exit('Invalid arguments given !!')

    if not (pat and templt):
        sys.exit('Invalid arguments given !!')

    return filedir, base_dir, max_files, pat, templt

def interact():
    base_dir=pat=templt=''
    max_files=-1
    print('Rene - Interactive Mode')
    res=input("press Enter to continue or type 'help' to display help and 'quit' to exit\n")
    if res=='help' :
        print(_help)
        return interact()
    elif res=='quit' :
        sys.exit()

    base_dir=input('> Base-directory (enter nothing for current directory) :')

    pat=input('> Pattern :')
    while not pat:
        print('This cannot be empty !!')
        pat=input('> Pattern :')

    templt=input('> Template :')
    while not templt:
        print('This cannot be empty !!')
        templt=input('> Template :')

    print('Rename only,\n\t1. files\n\t2. directory\n\t3. both')
    tmp_fd=input('> Enter [1/2/3] (enter nothing for files only) :')
    filedir = int(tmp_fd) if tmp_fd in ('1','2','3') else 1
    
    while True :
        temp=input('> Maximum files (-1 or nothing means no limit) :')
        try:
            max_files=int(temp) if temp else -1
            break
        except ValueError:
            print('Value should be an integer !!')

    return  filedir, base_dir, max_files, pat, templt

def main():
    filedir, base_dir, max_files, pat, templt = parse_args() if len(sys.argv)>1 else interact()
    base_path = Path(base_dir)
    if base_path.absolute() == Path(__file__).parent :
        show_error('You are trying to rename the files in the folder where this program is running',
            header='Warning',
            confirm_before_exit=True,
            confirm_msg='Are you sure about renaming the files ?',
        )
    # assignng static attributes
    static_attribs['base_dir']=base_dir
    static_attribs['parent']= base_path.parent.name
    try:
        rene(base_path, pat,templt,filedir, max_files)
    except Exception as e:
        sys.exit('Sorry, an error occured !!')
    input('press Enter to exit...')
    

if __name__ == "__main__":
    main()

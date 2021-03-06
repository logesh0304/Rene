# Rene
Rene is a simple python script to batch renaming files and folders with many functionalities and useful features. It is flexible, because it uses **regular-expression** and **glob** to search files by pattern. 

> A simple command for renaming **all files** in **test** directory to text files with names prefixed with its extension.  
`rene test ".*" "<:ext:>-<:name:>.txt"`

# What's new 
- It can also search files using **glob** pattern in addition to regex.
- It can now rename files in sub-directories also.
- Preview before renaming files.
- You can specify maximum number of files to rename.

# Download
Just download the *rene.py* file at **[here](https://github.com/logesh0304/Rene/releases/latest)**, then directly run it using command prompt or double clicking it if you installed python on your system. (the latter opens rene in interactive mode) 

>**Note:** This is made on **python 3.7** so you should have python version similar this installed on your system to run this script

# Usage
You can use rene in **command line**.

```
  rene [-glob] [ -f | -d | -a ]  [[-base] <basedir>] [-pat] <pattern> [-templt] <template> 
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

```

You can also use rene in **interactive mode** by executing the rene.py directly without giving any arguments or by using **-i** option in command line.

>**Note:** In this readme, files and directories are commonly known as files in some places.

# Constructing Template 
Template is a string representing the new name of each file matched by the given regex or glob pattern. Template can include *attributes* and *Incrementors*

>**Note:** If you don't know about regex or glob, google about it.

## Attributes
  You can include attributes like filename, extension, parent-directory in new name of the file. Attribute should be given in the form of `<:Attribute_name:>`. (i.e. between `<:` and `:>`)  

  Some attributes are common for all files (static attributes) and some are different (non-static attributes).

#### Static attributes :
- **base_dir**  -  base directory
- **parent**    -  parent of base directory

#### Non-static attributes :
- **name**      -  name of the file (without extension) or directory  

*below are only specific for files (not directory)*  

- **full_name** -  full name of the file with extension
- **ext**       -  extension of the file

## Incrementor 
Incrementor is a special feature of this script. It generates a value for each file by incrementing initial value. 

Incrementors are included in the form of `<:name [args]:>` ('name' represented here is the short name of the incrementor)  

**name** - the name of the incrementor  
**args** - arguments given to incrementor (this is optional)  

*Details about individual incrementors are given [below](#Types:)*

> **Arguments:** These are the values given to Incrementor. This is optionl, if it is not given default values are used. It can be given to incrementor either with keyword or in postional order.   
> - Keyword arguments are given in the form `key=value`. (Eg: `<:num init=34 step=2:>`).  
> - It should be given in correct order if it is given positionly (Eg: `<:num 12 2:>` is same as `<:num init=12 width=2:>`).  
> - We can give both keyword and posional arguments at same time , but posiotional arguments is interpreted first. (`<:alpha step=2 aa:>` is same as `<:alpha init=aa step=2:>`)  

**Note:** all itertor should have *init* as first parameter

### Types:
#### NumIncrementor
This gives series of *numbers* (1, 2, 3...)

**short-name** - num

 Arguments | discription | type | default-value
-----------|-------------|------|--------------
 init    | Initial value to this Incrementor | Number | 0  
 step    | Incrementing step | Number | 1    
 width   | Minmum width to the generated value. Remainig spaces are filled by 0. If the generated value is negative, minus sign should be in first| Positive-Number | based on initial value (if we want initial value is to be **1** and width is to be **5** we can give **00001** as initial value)  

<br>

#### AlphaIncrementor
This gives series of *alphabets* (a, b, c, ..., aab, aac, ...)

**short-name** - alpha

 Arguments | discription | type | default-value
-----------|-------------|------|--------------
 init    | Initial value to this Incrementor | String | A  
 step    | Incrementing step | Positive-Number | 1    
 case    | case of the generated alphabet. `lw` - lower-case, `up` - upper-case, `lu` - both | Any of string [lw, up, lu] | same as initial value   

<br>

#### AlnumIncrementor
This gives *alphanumeric* series (A0, A1, A2, ..., MX3, MX4, ...)

**short-name** - alnum

 Arguments | discription | type | default-value
-----------|-------------|------|--------------
 init      | Initial value to this Incrementor | Number+String | A0  
 step      | Incrementing step | Positive-Number | 1  
 case      | case of alphabet part. `lw` - lower-case, `up` - upper-case, `lu` - both | Any of string [lw, up, lu] | same as alphabet part in initial value
 intWidth  | Minimum width to integer part | Positive-Number | based on integer part in initial value
 intMaxCount | Maximum value for integer part | Positive-Number | based on integer part in inital value (i.e. no. of digits in integer part x 10)

<br>

>**Warning:** files renamed by this script cannot be undoed

# Contribution
Any contributions are welcome :smiley:

# License
This software is licensed with MIT License.
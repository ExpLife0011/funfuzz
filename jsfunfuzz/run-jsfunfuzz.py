#!/usr/bin/env python

#/* ***** BEGIN LICENSE BLOCK	****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is jsfunfuzz.
#
# The Initial Developer of the Original Code is
# Gary Kwong.
# Portions created by the Initial Developer are Copyright (C) 2006-2008
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# * ***** END LICENSE BLOCK	****	/
#
# Version History:
#
# April 2008 - 1.x:
#   Initial idea, previously called ./jsfunfuzz-moz18branch-start-intelmac
# June 2008 - 2.x:
#   Rewritten from scratch to support the new hg fuzzing branch.
# August 2008 - 3.0.x:
#   Rewritten from scratch again to support command-line inputs and consolidate
#   all existing jsfunfuzz bash scripts.
# September 2008 - 3.1.x:
# 	Support fuzzing v8 engine.
# December 2008 - 3.2.x:
#   Supports 1.9.1.x branch. Rip out 1.8.1.x code.
# January 2009 - 3.3.x:
#   Rework v8 support, add JavaScriptCore support.
# July 2009 - 4.x:
#   Python rewrite - only 1.9.1.x, TM and v8 planned for support. 1.9.0.x is
#   becoming obsolete in 5.5 months, mozTrunk is rarely fuzzed in favour of TM,
#   JavaScriptCore doesn't feel like a significant competing engine, and Safari
#   uses its own Nitro engine.
#
# Note:
#   If something screws up, trash the entire existing
#       ~/Desktop/jsfunfuzz-$compileType-$branchType folder.
#
# Receive user input on compileType and branchType.
#   compileType can be debug or opt.
#   branchType can be Gecko 1.9.1.x, TM or v8 engines.

import sys, os, subprocess, shutil
from time import gmtime, strftime

#######################
#  Variables (START)  #
#######################

supportedBranches = "[191|tm|v8]"  # Get 1.9.2 support through FIXMEFOR192.
verbose = True  # Turn this to True to enable verbose output for debugging.
def verbose():
    print
    print "DEBUG - output:"
def exceptionBadOs():
    raise Exception("Unknown OS - Platform is unsupported.")
def exceptionBadCompileType():
    raise Exception("Unknown compileType - choose from [dbg|opt].")
def exceptionBadPosixBranchType():
    raise Exception("Not a supported POSIX branchType")
def exceptionBadNtBranchType():
    raise Exception("Not a supported NT branchType")

# FIXME: Use optparse here. Move error() into optparse.

# The corresponding CLI requirements should be input, else output this error.
def error():
    print
    print "=========="
    print "| Error! |"
    print "=========="
    print
    print "General usage: ./run-jsfunfuzz.py [dbg|opt] " + supportedBranches
    print


# Accept dbg and opt parameters for compileType only.
if (sys.argv[1] == "dbg") or (sys.argv[1] == "opt"):
    compileType = sys.argv[1]
else:
    error()
    print "Your compileType variable is \'" + compileType + "\'"
    raise Exception("Only \'dbg\' or \'opt\' are accepted as compileType.")


# Accept appropriate parameters for branchType.
# FIXMEFOR192: Add 192 support here once the 1.9.2 branch is created.
if (sys.argv[2] == "191") or (sys.argv[2] == "tm") or (sys.argv[2] == "v8"):
    branchType = sys.argv[2]
else:
    error()
    print "Your branchType variable is \'" + branchType + "\'"
    raise Exception("Please double-check your branchType from " + \
                    supportedBranches + ".")


# Definitions of the different repository and fuzzing locations.
if os.name == "posix":
    def locations():
        repoFuzzing = "~/fuzzing/"     # Location of the fuzzing repository.
        repo191 = "~/mozilla-1.9.1/"   # Location of the 1.9.1 repository.
        repo192 = "~/mozilla-1.9.2/"   # Location of the 1.9.2 repository.
        repoTM = "~/tracemonkey/"      # Location of the tracemonkey repository.
        fuzzPathStart = "~/Desktop/jsfunfuzz-" # Start of the fuzzing directory.
        return repoFuzzing, repo191, repo192, repoTM, fuzzPathStart
elif os.name == "nt":
    def locations():
        # ~ is not used because in XP, ~ contains spaces in
        # "Documents and Settings".
        repoFuzzing = "/c/fuzzing/"    # Location of the fuzzing repository.
        repo191 = "/c/mozilla-1.9.1/"  # Location of the 1.9.1 repository.
        repo192 = "/c/mozilla-1.9.2/"  # Location of the 1.9.2 repository.
        repoTM = "/c/tracemonkey/"     # Location of the tracemonkey repository.
        fuzzPathStart = "/c/jsfunfuzz-"   # Start of the fuzzing directory.
        return repoFuzzing, repo191, repo192, repoTM, fuzzPathStart
else:
    exceptionBadOs()
    
repoFuzzing, repo191, repo192, repoTM, fuzzPathStart = locations()

if verbose:
    verbose()
    print "DEBUG - repoFuzzing, repo191, repo192, repoTM, fuzzPathStart are:"
    print "DEBUG - " + ", ".join(locations())

#####################
#  Variables (END)  #
#####################

# Expand the ~ folder on Linux/Mac.
if os.name == "posix":
    fuzzPath = os.path.expanduser(fuzzPathStart + compileType + "-" + \
                                  branchType + "/")

# Create the fuzzing folder.
try:
    os.makedirs(fuzzPath)
except OSError:
    error()
    raise Exception("The fuzzing path at \'" + fuzzPath + "\' already exists!")

# Change to the fuzzing directory.
os.chdir(fuzzPath)


# Methods to copy the entire js source directory.
def posixCopyJsTree(repo):
    shutil.copytree(os.path.expanduser(repo + "js/src/"),"compilePath")
def ntCopyJsTree(repo):
    shutil.copytree(repo + "js/src/","compilePath")

# Copy the entire js tree to the fuzzPath.
if os.name == "posix":
    if branchType == "191":
        posixCopyJsTree(repo191)
    elif branchType == "192":
        posixCopyJsTree(repo192)
    elif branchType == "tm":
        posixCopyJsTree(repoTM)
    else:
        exceptionBadPosixBranchType()()
elif os.name == "nt":
    if branchType == "191":
        ntCopyJsTree(repo191)
    elif branchType == "192":
        ntCopyJsTree(repo192)
    elif branchType == "tm":
        ntCopyJsTree(repoTM)
    else:
        exceptionBadNtBranchType()()
else:
    exceptionBadOs()

os.chdir("compilePath")


# Sniff platform and run different autoconf types:
if os.name == "posix":
    if os.uname()[0] == "Darwin":
        subprocess.call("autoconf213")
    elif os.uname()[0] == "Linux":
        subprocess.call("autoconf2.13")
elif os.name == "nt":
    subprocess.call("autoconf-2.13")
else:
    exceptionBadOs()


# Create objdirs within the compilePaths.
os.mkdir("dbg-objdir")
os.mkdir("opt-objdir")
os.chdir(compileType + "-objdir")


# Compile the first build.
if compileType == "dbg":
    subprocess.call(["../configure", "--disable-optimize", "--enable-debug"])
elif compileType == "opt":
    subprocess.call(["../configure", "--enable-optimize", "--disable-debug"])
else:
    exceptionBadCompileType()

def compileCopy(dbgOpt):
    # Run make using 2 cores.
    subprocess.call(["make", "-j2"])
    
    # Sniff platform and rename executable accordingly:
    if os.name == "posix":
        shellName = "js-" + dbgOpt + "-" + branchType + "-" + \
                    os.uname()[0].lower()
    elif os.name == "nt":
        shellName = "js-" + dbgOpt + "-" + branchType + "-" + os.name.lower()
    else:
        exceptionBadOs()
    
    # Copy js executable out into fuzzPath.
    shutil.copy2("js","../../" + shellName)
    
    return shellName

jsShellName = compileCopy(compileType)

# Change into compilePath directory for the opt build.
os.chdir("../")

if verbose:
    verbose()
    print "DEBUG - This should be the compilePath:"
    print "DEBUG - " + os.getcwdu()
    if "compilePath" in os.getcwdu():
        pass
    else:
        raise Exception("We are not in compilePath.")
    
# Compile the other build.
# No need to assign jsShellName here.
if compileType == "dbg":
    os.chdir("opt-objdir")
    subprocess.call(["../configure", "--enable-optimize", "--disable-debug"])
    compileCopy("opt")
elif compileType == "opt":
    os.chdir("dbg-objdir")
    subprocess.call(["../configure", "--disable-optimize", "--enable-debug"])
    compileCopy("dbg")
else:
    exceptionBadCompileType()

# Change into fuzzPath directory.
os.chdir("../../")

if verbose:
    verbose()
    print "DEBUG - This should be the fuzzPath:"
    print "DEBUG - " + os.getcwdu()
    if "fuzzPath" in os.getcwdu():
        pass
    else:
        raise Exception("We are not in fuzzPath.")


# FIXME v8 checkout.

# Copy over useful files that are updated in hg fuzzing branch.
if os.name == "posix":
    shutil.copy2(os.path.expanduser(repoFuzzing + "jsfunfuzz/jsfunfuzz.js"), ".")
    # FIXME: analysis.sh replacement ?
    shutil.copy2(os.path.expanduser(repoFuzzing + "jsfunfuzz/analysis.sh"), ".")
elif os.name == "nt":
    shutil.copy2(repoFuzzing + "jsfunfuzz/analysis.sh", ".")
else:
    exceptionBadOs()

print
print "============================================"
print "!  Fuzzing " + compileType + " " + branchType + " js shell builds now  !"
print "   DATE: " + time.asctime( time.localtime(time.time()) )
print "============================================"
print


# FIXME: of course have the 191 version of jsknownTM - sniff platform again. what about 192?
jsknownTM = repoFuzzing + "js-known/mozilla-central/"  # We use mozilla-central's js-known directories.
# Start fuzzing the newly compiled builds.
if verbose:
    print "jsShellName is " + jsShellName
    print "fuzzPath + jsShellName is " + fuzzPath + jsShellName
    print "python", "-u", \
                os.path.expanduser(repoFuzzing + "jsfunfuzz/multi_timed_run.py"), "1800", \
                os.path.expanduser(jsknownTM), fuzzPath + jsShellName, \
                "-j", os.path.expanduser(repoFuzzing + "jsfunfuzz/jsfunfuzz.js")
subprocess.call(["python", "-u", \
                os.path.expanduser(repoFuzzing + "jsfunfuzz/multi_timed_run.py"), "1800", \
                os.path.expanduser(jsknownTM), fuzzPath + jsShellName, \
                "-j", os.path.expanduser(repoFuzzing + "jsfunfuzz/jsfunfuzz.js")], \
                stdout=open("log-jsfunfuzz", "w"))
# FIXME: Implement 191, tm and v8 fuzzing for the above which right now is only hardcoded for tm. Works though. :) EDIT - 191 works too? change js-known to 191
# FIXME: I want to pipe stdout both to console output as well as to the file, just like the `tee` command.  stdout=subprocess.Popen(['tee', ...], stdin=subprocess.PIPE).stdin; of course
# def main(args=None):
# 	if args is None:
# 		args = []
# 
# 	tee = subprocess.Popen(["tee", "filename"],
# 		stdin=subprocess.PIPE, stdout=subprocess.PIPE)
# 	r = subprocess.call(["ls"], stdout=tee.stdin)
# 	output = tee.communicate()[0]
# 	print output
# 	print "r:", r
# FIXME: Implement the time command like in shell to the above. time.time then subtraction
# FIXME: Port above to windows. Basically take out expanduser?
# FIXME: make use of analysis.sh somewhere, not necessarily here.
# FIXME: Ensure debug builds are debug builds and opt builds are opt! Add unit test? test -Z 2 - js-dbg should start while opt should return an error code 2 - check subprocess returncode?
# FIXME: cleanup multiple elifs to if.. return. See below.
#>>> config = {}
#>>> def foo():
#...     config['boom'] = 'BANG'
#...     config['wat'] = 'YES'
#... 
#>>> def bar():
#...     config['boom'] = 'AAARGH'
#...     config['wat'] = 'NO'
#... 
#>>> {'a': foo, 'b': bar}['a']()
#>>> print config
#{'wat': 'YES', 'boom': 'BANG'}
#>>> {'a': foo, 'b': bar}['b']()
#>>> print config
#{'wat': 'NO', 'boom': 'AAARGH'}
#>>> 
#time python -u ~/fuzzing/jsfunfuzz/multi_timed_run.py 1800 ~/fuzzing/js-known/mozilla-central/ ~/Desktop/jsfunfuzz-$compileType-$branchType/js-$compileType-$branchType-intelmac -j ~/fuzzing/jsfunfuzz/jsfunfuzz.js | tee ~/Desktop/jsfunfuzz-$compileType-$branchType/log-jsfunfuzz

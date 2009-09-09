#!/usr/bin/env python


def ath(array):
    hash = {}
    for s in array:
        hash[s] = True
    return hash


knownHash = ath([

# Bug 403199
"nsSimpleNestedURI",

# Bug 467693
"nsStringBuffer",

# ...
"nsStorageStream",

# Bug 499607
"nsLineList",

# Bug 515278
"nsHtml5ElementName",
"AtomImpl"
])

# Things that are known to leak AND entrain smaller objects.
# If one of these leaks, leaks of small objects will not be reported.
knownLargeHash = ath([

# Bug 503989, bug 503991.  When removing, be sure to add to otherLargeHash below.
"nsGlobalWindow",
"nsDocument",

# Some Flash-related leak that I don't care about.  When removing, be sure to add to otherLargeHash below.  Will retest in Q1 2010.
"nsDocShell",

# Bug 397206
"BackstagePass",

# Bug 102229 or bug 419562
"nsDNSService",

# Bug 463724
"nsHTMLDNSPrefetch::nsDeferrals",
"nsDNSPrefetch",
"nsDNSAsyncRequest",
"nsHostResolver",

# Bug 424418
"nsRDFResource",

# Bug 417630 and friends
"nsJVMManager",

# Bug 509547
"nsJSChannel"

])

# Large items that
# - should be reported even if things in knownLargeHash leak
# - should quell the reporting of smaller objects
# XXX make this list permanent instead of having to remember to re-add things here
otherLargeHash = ath([
])


def amiss(logPrefix):
    currentFile = file(logPrefix + "-out", "r")
    sawLeakStats = False
    
    for line in currentFile:
        line = line.rstrip("\n")
        if (line == "== BloatView: ALL (cumulative) LEAK STATISTICS"):
            sawLeakStats = True
        # This line appears only if there are leaks
        if (line.endswith("Mean       StdDev")):
            break
    else:
        if sawLeakStats:
            #print "No leaks :)"
            pass
        else:
            print "Didn't see leak stats"
            pass
        currentFile.close()
        return False

    smallLeaks = ""
    largeKnownLeaks = ""
    largeOtherLeaks = ""

    for line in currentFile:
        line = line.strip("\x07").rstrip("\n").lstrip(" ")
        if (line == ""):
            break
        a = line.split(" ")[1]
        if a == "TOTAL":
            continue
        # print "Leaked at least one: " + a
        if a in knownLargeHash:
            largeKnownLeaks += "*** Leaked large object " + a + " (known)\n"
        if a in otherLargeHash:
            largeOtherLeaks += "*** Leaked large object " + a + "\n"
        if not a in knownHash:
            smallLeaks += a + "\n"

    if largeOtherLeaks != "":
        print "Leaked large objects:"
        print largeOtherLeaks
        # print "Also leaked 'known' large objects:"
        # print largeKnownLeaks
        currentFile.close()
        return True
    elif largeKnownLeaks != "":
        # print "(Known large leaks, and no other large leaks, so all leaks were ignored)"
        # print largeKnownLeaks
        currentFile.close()
        return False
    elif smallLeaks != "":
        print "Leaked:"
        print smallLeaks
        currentFile.close()
        return True
    else:
        # print "(Only known small leaks)"
        currentFile.close()
        return False

# print "detect_leaks is ready"

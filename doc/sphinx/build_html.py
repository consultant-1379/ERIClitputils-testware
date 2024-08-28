#!/usr/bin/env python

import os
import sys

currentDir = os.getcwd()
sourceDir = 'doc/sphinx/source/'
buildDir = 'target/site/'
sphinxPath = 'target/sphinx/'


def setupPythonPath(*paths):
    p = []
    for path in paths:
        sphinxAbsPath = os.path.abspath(os.path.join(currentDir, path))
        p.append(sphinxAbsPath)
    sys.path[:0] = p

if __name__ == '__main__':
    setupPythonPath(sphinxPath)
    from sphinx import cmdline
    cmdline.main(['-a',
                  os.path.abspath(os.path.join(currentDir, sourceDir)),
                  os.path.abspath(os.path.join(currentDir, buildDir))])

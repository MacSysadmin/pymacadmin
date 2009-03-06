#!/usr/bin/python
"""
Script by Chris Barker (chrisb@sneezingdog.com) to generate lists of Apple's
flat package format they use for OS and security updates and makes some useful
documentation

Copyright [2009] Chris Barker
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       
       http://www.apache.org/licenses/LICENSE-2.0
   
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

# FIXME: Find missing </li> in generated output
# TODO: Change HTML generation to serialize nested dicts so we can simplify the file handling code
# TODO: Move HTML to a separate template file?

import commands, os, sys, shutil
from BeautifulSoup import BeautifulSoup

def unFlattenPKG(pkg):
    dest = "/tmp/wtfupdate"
    flatStatus = commands.getstatusoutput("/usr/sbin/pkgutil --expand \"%s\" \"%s\"" % (pkg, dest) )
    return dest

def getSUDescription(pkg):
    su_desc = pkg + '/Resources/English.lproj/SUDescription.html'
    
    if not os.path.exists(su_desc):
        return "<i>no description</i>"
    
    sud = open( su_desc, 'r' )
    soup = BeautifulSoup(sud)
    sud.close()
    return soup.body

def getScripts(pkg, htmloutput):
    for fileName in os.listdir(pkg):
        if os.path.splitext(fileName)[1] == '.pkg':
            htmloutput.write("""<ul><li><b> %s Scripts</b>\n""" % fileName)
            for script in os.listdir(pkg + '/' + fileName + '/Scripts'):
                if os.path.isfile(pkg + '/' + fileName + '/Scripts' + '/' + script):
                    htmloutput.write("""<ul><li>\n""" +str(script))
                    htmloutput.write("""<pre>\n""")
                    scriptContent = open(pkg + '/' + fileName + '/Scripts' + '/' + script, 'r')
                    htmloutput.writelines(scriptContent.readlines())
                    scriptContent.close()
                    htmloutput.write("""</pre></li></ul>\n""")
                elif os.path.isdir(pkg + '/' + fileName + '/Scripts' + '/' + script) and str(script) != 'Tools':
                    htmloutput.write("""<ul><li>\n""" + str(script))
                    for subscript in os.listdir(pkg + '/' + fileName + '/Scripts' + '/' + script):
                        htmloutput.write("""<ul><li>\n""" + str(subscript))
                        htmloutput.write("""<pre>\n""")
                        scriptContent = open(pkg + '/' + fileName + '/Scripts' + '/' + script + '/' + subscript, 'r')
                        htmloutput.writelines(scriptContent.readlines())
                        scriptContent.close()
                        htmloutput.write("""</pre></li></ul>\n""")
                    htmloutput.write("""</li></ul>\n""")
            htmloutput.write("""</li></ul>\n""")
    return htmloutput

def getFileList(pkg, fileName, htmloutput):
    bom = pkg + '/' + fileName + '/Bom'
    paths = commands.getstatusoutput("/usr/bin/lsbom %s | cut -f 1" % bom )
    listofPaths = paths[1].split('\n')
    
    listofPaths.sort(key=str.lower)
    htmloutput.write("<ul class=\"listexpander\">\n")
    depth=0
    
    for item in listofPaths:
        if item == '.':
            htmloutput.write("""<li><b> %s Files</b>\n""" % fileName)
        elif item.count('/') == depth:
            htmloutput.write("""<li>%s\n""" % item)
        elif item.count('/') > depth:
            htmloutput.write("""<ul><li>%s\n""" % item)
            depth = item.count('/')
        elif item.count('/') < depth:
            for i in range(item.count('/'), depth):
                htmloutput.write("""</li></ul>\n""")
            
            htmloutput.write("""</li><li>%s\n""" % item)
            depth = item.count('/')
    
    for i in range(0, depth):
        htmloutput.write("""</li></ul>\n""")
        htmloutput.write("""</li></ul>\n""")

    
    return htmloutput

def writeHeaders(htmloutput):
    lines = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>wtfupdate</title>

        <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.1/jquery.min.js" type="text/javascript" charset="utf-8"></script>
        <script>
            jQuery(function() {
                // Look for <li> clicks and toggle the visibility of their child lists:
                jQuery("li").live("click", function () { $(this).children("ul").toggle(); } );

                // Hide second+ level lists to start:
                jQuery("ul > li > ul").css("display", "none");
                
                // Add a (#) descendent count:
                jQuery("li > ul").each(function() { $(this).before(" (" + $(this).find("li").length + ")") });
            });
        </script>
        <style>    
            body{
                margin:0;
                padding:0;
                background:#f1f1f1;
                font:70% Arial, Helvetica, sans-serif;
                color:#555;
                line-height:150%;
                text-align:left;
            }
            a{
                text-decoration:none;
                color:#057fac;
            }
            a:hover{
                text-decoration:none;
                color:#999;
            }
            h1{
                font-size:140%;
                margin:0 20px;
                line-height:80px;
            }
            #container{
                margin:0 auto;
                width:680px;
                background:#fff;
                padding-bottom:20px;
            }
            #content{margin:0 20px;}
            p{
                margin:0 auto;
                width:680px;
                padding:1em 0;
            }
        </style>
    </head>
    
    <body>
    """
    htmloutput.writelines(lines)
    return htmloutput

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print 'Usage: %s file.pkg output.html' % sys.argv[0]
        sys.exit(1)

    pkg_file, html_file = sys.argv[1:3]
    
    htmloutput = open(html_file, 'w')
    writeHeaders(htmloutput)
    
    pkg = unFlattenPKG(pkg_file)
    
    for i in getSUDescription(pkg):
        htmloutput.writelines(str(i))
    
    getScripts(pkg, htmloutput)

    if os.path.exists(pkg + "/Bom"):
        getFileList(pkg, "", htmloutput)
    
    for fileName in os.listdir(pkg):
        if os.path.splitext(fileName)[1] == '.pkg':
            getFileList(pkg, fileName, htmloutput)
    
    htmloutput.close()
    
    shutil.rmtree(pkg)
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010-2011 Various Authors
# Copyright 2010 Johannes Weißl
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import sys
import re
import os.path
import urllib2
from optparse import OptionParser

# Some letters don't have a decomposition, but can't be composed on all
# keyboards. This dictionary maps them to an ASCII character which
# *looks* similar.
special_decompositions = {
    u'Æ': u'A',
    u'Ð': u'D',
    u'×': u'x',
    u'Ø': u'O',
    u'Þ': u'P',
    u'ß': u'B',
    u'æ': u'a',
    u'ð': u'd',
    u'ø': u'o',
    u'þ': u'p',
# Various punctation/quotation characters
    u'‐': u'-',
    u'‒': u'-',
    u'–': u'-',
    u'−': u'-',
    u'—': u'-',
    u'―': u'-',
    u'‘': u"'",
    u'’': u"'",
    u'′': u"'",
    u'“': u'"',
    u'”': u'"',
    u'″': u'"',
    u'〃': u'"',
    u'…': u'.',
}

def parse_unidata(f):
    u = {}
    for line in f:
        d = line.rstrip('\n').split(';')
        cp = int(d[0], 16)
        u[cp] = {}
        u[cp]['name'] = d[1]
        decomp = d[5]
        if decomp:
            m = re.match(r'<.*> (.*)', decomp)
            u[cp]['compat'] = bool(m)
            if m:
                decomp = m.group(1)
            u[cp]['decomp'] = [int(x, 16) for x in decomp.split(' ')]
        else:
            u[cp]['decomp'] = []
    return u

def unidata_expand_decomp(unidata):
    def recurse(k):
        if k not in unidata or not unidata[k]['decomp']:
            return [k]
        exp = []
        for d in unidata[k]['decomp']:
            exp += recurse(d)
        return exp
    for k in unidata.keys():
        exp = recurse(k)
        if exp != [k]:
            unidata[k]['decomp'] = exp

def unidata_add_mapping(unidata, mapping):
    for k, v in mapping.items():
        unidata[ord(k)]['decomp'] = [ord(v)]

def is_diacritical_mark(c):
    return c >= 0x0300 and c <= 0x036F

def filter_unidata(unidata, include):
    for k, v in unidata.items():
        if k in include:
            continue
        if not v['decomp']:
            del unidata[k]
            continue
        b = v['decomp'][0]
        if unichr(b) == u' ' or is_diacritical_mark(b):
            del unidata[k]
            continue
        has_accents = False
        for d in v['decomp'][1:]:
            if is_diacritical_mark(d):
                has_accents = True
                break
        if not has_accents:
            del unidata[k]

def output(unidata, f):
    buf = '''/* This file is automatically generated. DO NOT EDIT!
Instead, edit %s and re-run. */

static struct {
	uchar composed;
	uchar base;
} unidecomp_map[] = {
''' % os.path.basename(sys.argv[0])
    for k in sorted(unidata.keys()):
        b = unidata[k]['decomp'][0]
        buf += '\t{ %#6x, %#6x },\t// %s -> %s,\t%s\n' % \
            (k, b,
            unichr(k).encode('utf-8'),
            unichr(b).encode('utf-8'),
            ', '.join([' %s (%x)' %
                (unichr(d).encode('utf-8'), d)
                    for d in unidata[k]['decomp'][1:]]))
    buf += '};'
    f.write(buf+'\n')

def main(argv=None):

    if not argv:
        argv = sys.argv

    parser = OptionParser(usage='usage: %prog [-w] [-o unidecomp.h]')
    parser.add_option('-w', '--wget', action='store_true',
        help='get unicode data from unicode.org')
    parser.add_option('-o', '--output',
        help='output file, default stdout')
    (options, args) = parser.parse_args(argv[1:])

    urlbase = 'http://unicode.org/Public/UNIDATA/'
    unidata_filename = 'UnicodeData.txt'

    if not os.path.exists(unidata_filename) and not options.wget:
        parser.error('''need %s in the current directory, download
from unicode.org or use `--wget' option.''' % unidata_filename)

    if options.wget:
        unidata_file = urllib2.urlopen(urlbase+unidata_filename)
    else:
        unidata_file = open(unidata_filename, 'rb')

    unidata = parse_unidata(unidata_file)
    unidata_file.close()

    unidata_add_mapping(unidata, special_decompositions)
    unidata_expand_decomp(unidata)
    filter_unidata(unidata, [ord(x) for x in special_decompositions])

    outfile = sys.stdout
    if options.output:
        outfile = open(options.output, 'wb')
    output(unidata, outfile)
    if options.output:
        outfile.close()

if __name__ == '__main__':
    sys.exit(main())

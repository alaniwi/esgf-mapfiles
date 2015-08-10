"""
This is a utility that assists when editing the config.ini file that is 
used with esg_mapfiles, by identifying any facet values that are present 
in a list of datasets but not in the config file.

It takes the config filename and project ID as command-line arguments,
and the list of datasets on standard input, and it outputs lists of missing 
facet values that may need to be added to the config file (as well as 
lists of unused values).

For example:

$ cat dsets
cmip5.output2.MOHC.HadGEM2-ES.historical.3hr.atmos.3hr.r2i1p1#v20110323
cmip5.output2.MOHC.HadGEM2-ES.historical.3hr.land.3hr.r2i1p1#v20110323
cmip5.output2.MOHC.HadGEM2-ES.historical.3hr.land.3hr.r2i1p1#v20111007
...

$ esg_mapfiles_check_vocab config.ini cmip5 < dsets

(version in the list also allowed to be omitted or separated with a '.' 
instead of '#')

If there are missing options, there will be lines in the output saying
"USED BUT DISALLOWED", and the return value will be 1.  Otherwise returns 0 
when invoked with correct usage.

"""

import re
import sys
import string
import ConfigParser


def get_conf(conf_file):
    cfg = ConfigParser.ConfigParser()
    if not cfg.read(conf_file):
        raise ValueError("could not open config file %s" % conf_file)
    return cfg

def strip_hash_to_end(strng):
    try:
        return strng[:strng.index("#")]
    except ValueError:
        return strng

def get_list_from_stdin():
    # (use readlines as xreadlines needs 2 x ctrl-D when reading from terminal)
    return [line.replace("\n", "") for line in sys.stdin.readlines()]

def id_components(id):
    return strip_hash_to_end(id).split(".")

def get_facets_from_config(conf, project):
    return id_components(conf.get(project, "dataset_ID"))

is_version = re.compile("(v[\d]+|latest)$").match

def get_facet_values_from_dsets(dsets, facets):
    all_values = {}
    for facet in facets:
        all_values[facet] = set()
    for dset in dsets:
        values = id_components(dset)
        # accept dataset with .v{version} (instead of #{version}) at end
        if len(values) == len(facets) + 1 and is_version(values[-1]):
            values = values[:-1]
        # but aside from that, must be right number of facets
        if len(values) != len(facets):
            print "WARNING: skipping dataset %s: wrong number of facets" % dset
        for pos, val in enumerate(values):
            all_values[facets[pos]].add(val)
    return all_values

def get_facet_values_from_config(conf, project, facets):
    all_values = {}
    for facet in facets:        
        key = "%s_options" % facet
        if conf.has_option(project, key):
            all_values[facet] = set(re.split(",\s+", conf.get(project, key)))
        else:
            all_values[facet] = None
    return all_values

def comma_list(myset):
    l = list(myset)
    l.sort()
    return string.join(l, ", ")

def compare_values(project, facets, vals_used, vals_conf):
    any_disallowed = False
    for facet in facets:
        allowed = vals_conf[facet]
        used = vals_used[facet]
        prefix = '[%s]%s_options:' % (project, facet)
        if allowed == None:
            print prefix, "no list of values configured"
            print prefix, "used: ", comma_list(used)
        else:
            disallowed = used.difference(allowed)
            unused = allowed.difference(used)

            print prefix, "allowed: ", comma_list(allowed)
            print prefix, "used: ", comma_list(used)

            if disallowed:
                print prefix, "USED BUT DISALLOWED: ", comma_list(disallowed)
                any_disallowed = True
                print prefix, "updated allowed list: ", comma_list(used.union(allowed))

            if unused:
                print prefix, "allowed but unused: ", comma_list(unused)
        print
    if any_disallowed:
        print ">>>> THERE WERE DISALLOWED VALUES USED <<<<"
        print ">>>> SEARCH FOR 'DISALLOWED' ABOVE <<<<"
    return any_disallowed

def main():
    try:
        conf_file, project = sys.argv[1:]
    except ValueError:
        print __doc__
        sys.exit(2)
    if sys.stdin.isatty():
        print "give dataset IDs one per line, ctrl-D to terminate"
        print "(did you mean to redirect input from a file?)"
    
    conf = get_conf(conf_file)
    facets = get_facets_from_config(conf, project)
    dsets = get_list_from_stdin()
    facet_values_used = get_facet_values_from_dsets(dsets, facets)
    facet_values_conf = get_facet_values_from_config(conf, project, facets)
    any_disallowed = compare_values(project, facets, facet_values_used, facet_values_conf)
    if any_disallowed:
        sys.exit(1)

if __name__ == '__main__':
    main()




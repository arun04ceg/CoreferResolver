import sys
sys.path.insert(0, "/home/baskar/COREF_RESOLUTION_DRY/")
from CR import CR
from optparse import OptionParser


def main(options):
    #listfile, responsedir = "input_list_file.txt", "output/" 
    listfile, responsedir = options
    #Get Input Files
    input_files = get_input_filenames(listfile)
    #Coref Resolve
    coref_resolve(input_files, responsedir)
   
def coref_resolve(input_files, responsedir):
    for filename in input_files:
        print "Processing: %s" % filename
        CR_instance = CR(filename)
        CR_instance.apply_rules()
        CR_instance.write_output(responsedir)    

def get_input_filenames(listfile):
    input_files = []
    in_file = open(listfile)
    for line in in_file:
        line = line.strip()
        input_files.append(line)
    in_file.close()
    return input_files

if __name__ == "__main__":
    options = sys.argv[1:]
    if len(options) != 2:
       print "Improper set of inputs are given."
       print "The command line format is 'python2.6 coreference.py <listfile> <responsedir>'"
       print "Exiting."
       sys.exit(2)
    else:
        main(options) 

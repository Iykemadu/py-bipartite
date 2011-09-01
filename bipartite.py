# ===================================================================
# Random bipartite graph generation with prescribed degree
# distribution
#
# (C) 2011, Bruno Quoitin (bruno.quoitin@umons.ac.be)
# ===================================================================
#
# This program is organized as follows:
#
#   The main entry is in function 'main' which is responsible for
#   parsing the command line.
#
#   The user provides a variable number of operations along with
#   their arguments. More details about the supported operations
#   and their arguments can be obtained by running the program
#   without argument (see function 'usage'). All operations are
#   defined in the data structure 'operations').
#
#   The most important operation is named 'generate' (see function
#   'bipartite_op_generate'). This operation generates a bipartite
#   graph using degree sequences for the L2/L3 levels that are
#   obtained from 2 Pareto distributions. This operation requires
#   the user to provide the number of nodes, exponent (alpha) and
#   scale (beta) parameters for each level. There is a total of 6
#   arguments. Here is an example
#
#     python bipartite.py generate:100:2:2:120:-1:1 plot
#
#   The above invocation contains an undefined parameter (alpha for
#   the L3 level). This parameter will be derived automatically (if
#   possible). The generated graph will the be displayed.
#
#   Other important operations are
#     'giant' which extracts the largest connected component (see
#       function 'bipartite_op_giant'),
#     'save' which allows to save the generated graph into a file
#       (see function 'bipartite_op_save')
#     'project' which projects the bipartite graph onto the L3 level
#       ( see function 'bipartite_op_project').
#
# ===================================================================


import igraph
import igraph.drawing
import numpy
import random
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from pareto import Pareto
from mrinfo import MRINFO


# -----[ Constants ]-------------------------------------------------
TYPE_L2= False
TYPE_L3= True
COLOR_DICT= {TYPE_L2:"blue", TYPE_L3:"green"}
SHAPE_DICT= {TYPE_L2:"rectangle", TYPE_L3:"circle"}


# -----[ Global options ]--------------------------------------------
verbosity = 0
max_redraws = 1000000


# -----[ log ]-------------------------------------------------------
# Display log message if current verbosity level is higher or equel
# than level in argument.
# -------------------------------------------------------------------
def log(level, msg):
    if (verbosity >= level):
        print msg
    return


# -----[ error ]-----------------------------------------------------
# Display error message and exit with error
# -------------------------------------------------------------------
def error(msg):
    print >> sys.stderr, "Error: %s" % (msg)
    sys.exit(-1)
    return


# -----[ bipartite_cm ]----------------------------------------------
# Generate a bipartite graph using the provided L2 and L3 degree
# sequences. The total L2 and L3 degrees MUST match.
# -------------------------------------------------------------------
def bipartite_cm(degrees2, degrees3):
    vertices_types= []
    edges= []

    td2= 0
    td3= 0

    stubs2= []
    stubs3= []
    id= 0

    # Generate L2/L3 stubs according to the respective prescribed
    # degree sequences
    for i in range(len(degrees2)):
        vertices_types.append(TYPE_L2)
        td2+= degrees2[i]
        for j in range(degrees2[i]):
            stubs2.append((id, j))
        id+= 1
        
    for i in range(len(degrees3)):
        vertices_types.append(TYPE_L3)
        td3+= degrees3[i]
        for j in range(degrees3[i]):
            stubs3.append((id, j))
        id+= 1

    # Check that total L2/L3 degrees match
    if (td2 != td3):
        raise Exception("Total L2 degree does not match total L3 degree")

    # Shuffle L3 stubs
    random.shuffle(stubs3)
    log(1, "lengths: %d ; %d" % (len(stubs2), len(stubs3)))

    # Connect L2 and L3 stubs
    for i in range(len(stubs2)):
        log(2, "connect L2/L3 stubs (%d, %d)" % (stubs2[i][0], stubs3[i][0]))
        edges.append((stubs2[i][0], stubs3[i][0]))

    # Generate Bipartite graph
    g= igraph.Graph.Bipartite(vertices_types, edges)

    return g


# -----[ random_pareto_matching_degrees ]----------------------------
# Generate matching L2/L3 degree sequences using Pareto distribution
# with provided L2/L3 alpha exponents.
# -------------------------------------------------------------------
def random_pareto_matching_degrees(l2_params, l3_params):
    degrees2= []
    degrees3= []
    td2= 0
    td3= 0

    # Initialize L2/L3 Pareto classes
    p2= Pareto(l2_params.get_alpha(), l2_params.get_beta())
    p3= Pareto(l3_params.get_alpha(), l3_params.get_beta())

    # Generate L2 degree sequence
    for i in range(l2_params.get_n()):
        r= int(round(p2.random()))
        degrees2.append(r)
        td2+= r

    # Generate L3 degree sequence
    for i in range(l3_params.get_n()):
        r= int(round(p3.random()))
        degrees3.append(r)
        td3+= r

    log(1, "# Total degrees: td2=%d  vs  td3=%d" % (td2, td3))

    # Try to ensure total L2/L3 degrees match by re-drawing the
    # degree for randomly picked pairs of L2/L3 nodes
    #
    # Note: another strategy might be to try to add nodes for the
    #       smallest degree distribution until a match is found.
    #       I need to investigate this part further...
    num_redraws= 0
    while (td2 != td3):
        i= random.randint(0, l2_params.get_n()-1)
        j= random.randint(0, l3_params.get_n()-1)
        td2-= degrees2[i]
        td3-= degrees3[j]
        degrees2[i]= int(round(p2.random()))
        degrees3[j]= int(round(p3.random()))
        td2+= degrees2[i]
        td3+= degrees3[j]
        log(2, "#i=%d,j=%d   td2=%d  vs  td3=%d" % (i, j, td2, td3))
        num_redraws+= 1
        if (num_redraws > max_redraws):
            error("maximum redraws limit was reached")
            return None

    log(1, "  Number of redraws required = %d" % (num_redraws))
    return (degrees2, degrees3)


def test_redraw_count(n2, n3, a2, a3, num_tests):
    redraw_freq= {}
    max_redraw= 0

    for i in range(num_tests):
        if i % 2 == 0:
            print >> sys.stderr, "\r%.2f %%" % (100.0*i/num_tests),
            sys.stderr.flush()
        (degrees2, degrees3, redraw)= \
            random_pareto_matching_degrees(n2, n3, a2, a3)
        if redraw not in redraw_freq:
            redraw_freq[redraw]= 1
        else:
            redraw_freq[redraw]+= 1
        if redraw > max_redraw:
            max_redraw= redraw
    print >> sys.stderr, "\r%.2f %%" % (100.0)
    cumul= 0
    print "-1\t0\t0"
    for i in range(-1, max_redraw+1):
        if i in redraw_freq:
            v= redraw_freq[i]
            cumul+= v
            print "%d\t%d\t%.20f" % (i, v, float(cumul)/num_tests)


def test_stats(n2, n3, a2, a3):
    b2= 1
    b3= 1
    p2= Pareto(a2, b2)
    p3= Pareto(a3, b3)
    print " L2: expectation = %.20f" % (p2.expectation())
    print "     variance = %.20f" % (p2.variance())
    print " L3: expectation = %.20f" % (p3.expectation())
    print "     variance = %.20f" % (p3.variance())
    return
    

# -----[ bipartite_op_generate ]-------------------------------------
#
# -------------------------------------------------------------------
def bipartite_op_generate(g, params):
    if len(params) != 6:
        error("invalid number of arguments for \"generate\"")

    # Obtain degree distribution parameters
    l2_params= DegreeSeqParams(int(params[0]), float(params[1]), float(params[2]))
    l3_params= DegreeSeqParams(int(params[3]), float(params[4]), float(params[5]))

    # Check there is at most one undefined parameter
    if (l2_params.num_undefined() + l3_params.num_undefined() > 1):
        error("too many (%d) undefined parameters (1 max)" % (num_undefined))

    # Determine L2/L3 exponent automatically from other parameters
    l3_params.solve_undefined(l2_params)
    l2_params.solve_undefined(l3_params)

    print "  L2 Parameters:"
    l2_params.dump()
    print "  L3 Parameters:"
    l3_params.dump()

    # Check expected number of edges at level 2
    # against expected number of edges at level 3
    print "  Expected total L2 degree = %.20f" % (l2_params.exp_tot_degree())
    print "  Expected total L3 degree = %.20f" % (l3_params.exp_tot_degree())

    (degrees2, degrees3)= \
        random_pareto_matching_degrees(l2_params, l3_params)

    return bipartite_cm(degrees2, degrees3)


# -----[ bipartite_op_plot ]-----------------------------------------
#
# -------------------------------------------------------------------
def bipartite_op_plot(g, params):
    if (len(params) < 1):
        filename= params[0]
    else:
        filename= None
    layout= g.layout("fr")
    #layout= g.layout("kk")
    if "type" in g.vs.attribute_names():
        g.vs["color"]= [COLOR_DICT[type] for type in g.vs["type"]]
        g.vs["shape"]= [SHAPE_DICT[type] for type in g.vs["type"]]
    else:
        g.vs["color"]= [COLOR_DICT[TYPE_L3] for idx in range(g.vcount())]
        g.vs["shape"]= [SHAPE_DICT[TYPE_L3] for idx in range(g.vcount())]
    if filename:
        igraph.drawing.plot(g, layout=layout, target=filename)
    else:
        igraph.drawing.plot(g, layout=layout)
    return g


# -----[ bipartite_op_save ]-----------------------------------------
#
# -------------------------------------------------------------------
def bipartite_op_save(g, params):
    if (g == None):
        error("no graph to save")
    filename= params[0]
    format= params[1]
    print "  Save graph to file \"%s\" with format \"%s\"" \
          % (filename, format)
    if (format == "graphml"):
        g.write_graphml(filename)
    elif (format == "graphmlz"):
        g.write_graphmlz(filename)
    elif (format == "dot"):
        g.write_dot(filename)
    elif (format == "edgelist"):
        g.write_edgelist(filename)
    else:
        error("unknown file format \"%s\"" % (format))
    return g


# -----[ bipartite_op_check ]----------------------------------------
#
# -------------------------------------------------------------------
def bipartite_op_check(g, params):
    if (g == None):
        error("no graph to check")
    if (g.is_connected()):
        print "  Graph is connected"
    else:
        print "  Graph is not connected"
    clusters= g.clusters()
    print "  Number of connected components = %d" % (len(clusters))
    giant= clusters.giant()
    print "  Size of largest component = %d" % (giant.vcount())
    # Number of parallel edges ?
    return g


# -----[ bipartite_op_giant ]----------------------------------------
# Extract largest connected component
# -------------------------------------------------------------------
def bipartite_op_giant(g, params):
    if (g == None):
        error("no graph to extract largest component")
    print "  Extract largest connected component"
    return g.clusters().giant()


# -----[ bipartite_op_project ]--------------------------------------
# Project bipartite graph onto L3
# -------------------------------------------------------------------
def bipartite_op_project(g, params):
    if (g == None):
        error("no graph to project")
    print "  Project onto L3"
    (g_l2, g_l3)= g.bipartite_projection()
    return g_l3


# -----[ bipartite_op_orphans ]--------------------------------------
# Remove orphans (o-degree) nodes
# -------------------------------------------------------------------
def bipartite_op_orphans(g, params):
    if (g == None):
        error("no graph to remove orphans from")
    orphans= [idx for idx in range(g.vcount()) if g.degree(idx)==0]
    g.delete_vertices(orphans)
    print "  Number of orphan nodes removed: %d" % (len(orphans))
    return g


# -----[ bipartite_op_stats ]----------------------------------------
# Compute some statistics:
# - number of vertices/edges
# - overall/L2/L3 degree frequency distribution
# - Pareto maximum likelyhood estimators
# -------------------------------------------------------------------
def bipartite_op_stats(g, params):
    if (g == None):
        error("no graph to compute statistics")
    bipartite= g.is_bipartite()
    if (bipartite):
        l2_vertices= [idx for idx in range(g.vcount()) if not(g.vs["type"][idx])]
        l3_vertices= [idx for idx in range(g.vcount()) if g.vs["type"][idx]]
    print "  Number of vertices: %d" % (g.vcount())
    if (bipartite):
        print "  Number of L2 vertices: %d" % (len(l2_vertices))
        print "  Number of L3 vertices: %d" % (len(l3_vertices))
    print "  Number of edges: %d" % (g.ecount())

    degrees= g.degree()
    if (bipartite):
        l2_degrees= g.degree(l2_vertices)
        l3_degrees= g.degree(l3_vertices)
    max_degree= g.maxdegree()
    print "  Highest degree"
    print "    overall: %d" % (max_degree)
    if (bipartite):
        print "    L2: %d" % (g.maxdegree(l2_vertices))
        print "    L3: %d" % (g.maxdegree(l3_vertices))
    degrees_hist= numpy.histogram(degrees, bins=max_degree,
                                  range=(0, max_degree))
    if (bipartite):
        l2_degrees_hist= numpy.histogram(l2_degrees, bins=max_degree,
                                         range=(0, max_degree))
        l3_degrees_hist= numpy.histogram(l3_degrees, bins=max_degree,
                                         range=(0, max_degree))

    print "  Maximum Likelihood Estimator:"
    print "    overall (beta=1): %.20f" % (Pareto.mle(degrees))
    if (bipartite):
        l2_mle= {}
        l2_mle[1]= Pareto.mle(l2_degrees)
        print "    L2 (beta=1): %.20f" % (l2_mle[1])
        l2_mle[2]= Pareto.mle(l2_degrees, 2.0)
        print "    L2 (beta=2): %.20f" % (l2_mle[2])
        l2_mle[3]= Pareto.mle(l2_degrees, 3.0)
        print "    L2 (beta=3): %.20f" % (l2_mle[3])
        l3_mle= Pareto.mle(l3_degrees)
        print "    L3 (beta=1): %.20f" % (l3_mle)

    plt.figure()
    #plt.suptitle(???)
    plt.subplots_adjust(hspace=0.35)
    if (bipartite):
        plt.subplot(3, 2, 1)
    else:
        plt.subplot(1, 2, 1)
    plt.title("Overall degree distribution", fontsize=10)
    plt.hist(degrees, bins=max_degree, range=(0, max_degree), cumulative=False, normed=False, histtype='bar')
    if (bipartite):
        plt.subplot(3, 2, 2)
    else:
        plt.subplot(1, 2, 2)
    plt.title("(log-log)", fontsize=10)
    plt.grid()
    plt.loglog(range(0, max_degree), degrees_hist[0], 'o')
    if (bipartite):
        plt.subplot(3, 2, 3)
        plt.title("L2 degree distribution", fontsize=10)
        plt.hist(l2_degrees, bins=max_degree, range=(0, max_degree), cumulative=False, normed=False, histtype='bar')
        plt.subplot(3, 2, 4)
        plt.title("(log-log)", fontsize=10)
        plt.grid()
        plt.loglog(range(0, max_degree), l2_degrees_hist[0], 'o')
        for beta in [1, 2, 3]:
            bloub= []
            p= Pareto(l2_mle[beta], beta)
            n= 0
            for k in l2_degrees:
                if k >= beta:
                    n+= 1
            for k in range(beta, max_degree, 1):
                bloub.append(p.pdf(k)*n)
            plt.plot(range(beta, max_degree, 1), bloub)
        plt.subplot(3, 2, 5)
        plt.title("L3 degree distribution", fontsize=10)
        plt.hist(l3_degrees, bins=max_degree, range=(0, max_degree), cumulative=False, normed=False, histtype='bar')
        plt.subplot(3, 2, 6)
        plt.title("(log-log)", fontsize=10)
        plt.grid()
        plt.loglog(range(0, max_degree), l3_degrees_hist[0], 'o')
        bloub= []
        p= Pareto(l3_mle)
        for k in range(1, max_degree, 1):
            bloub.append(p.pdf(k)*len(l3_degrees))
        print bloub
        plt.plot(range(1, max_degree, 1), bloub)

    plt.show()

    return g


# -----[ bipartite_op_mrinfo ]---------------------------------------
# Load an 'mrinfo' file
# -------------------------------------------------------------------
def bipartite_op_mrinfo(g, params):
    filename= params[0]
    print "  Load graph \"%s\"" % (filename)
    return MRINFO.load(filename)


# -----[ bipartite_op_toy ]------------------------------------------
# Generates a toy bipartite graph.
# This is mainly used for demo/debugging.
# -------------------------------------------------------------------
def bipartite_op_toy(g, params):
    print "  Generate toy bipartite graph"
    return bipartite_cm([2, 2, 3, 3, 2], [1, 1, 2, 2, 1, 2, 3])


# -------------------------------------------------------------------
# Define supported graph transformations/operations
#   1st param = function of (graph, typle of params), must return
#               new graph or None
#   2nd param = number of arguments
# -------------------------------------------------------------------
operations= {
    "check":(bipartite_op_check, (0, 0)),
    "generate":(bipartite_op_generate, (6, 6)),
    "giant":(bipartite_op_giant, (0, 0)),
    "mrinfo":(bipartite_op_mrinfo, (1, 1)),
    "orphans":(bipartite_op_orphans, (0, 0)),
    "plot":(bipartite_op_plot, (0, 1)),
    "project":(bipartite_op_project, (0, 0)),
    "save":(bipartite_op_save, (2, 2)),
    "stats":(bipartite_op_stats, (0, 0)),
    "toy":(bipartite_op_toy, (0, 0)),
    }


# -----[ usage ]-----------------------------------------------------
# Display program usage help
# -------------------------------------------------------------------
def usage():
    print "Usage: python bipartite.py [ OPERATION [ OPERATION [ ... ] ] ]"
    print
    print "  where OPERATION is one of"
    print
    print "  - generate:N2:A2:B2:N3:A3:B3"
    print "      Produces a bipartite graph L2/L3 degrees obtained"
    print "      by sampling 2 Pareto distributions."
    print
    print "      N2: number of L2 nodes (integer, > 0)"
    print "      A2: L2 exponent parameter (float, > 1)"
    print "      B2: L2 scale parameter (float, >= 1)"
    print "      N3: number of L3 nodes (integer, > 0)"
    print "      A3: L3 exponent parameter (float, > 1)"
    print "      B3: L3 scale parameter (float, >= 1)"
    print "      one of the above parameters can be left undefined (-1)"
    print
    print "  - project"
    print "      Produces the L3 projection of a pre-computed"
    print "      bipartite graph."
    print
    print "  - check"
    print "      Performs connectivity checks on a pre-computed graph."
    print
    print "  - giant"
    print "      Extract the largest connected component of a pre-computed graph."
    print
    print "  - mrinfo:FILENAME"
    print "      Load a bipartite graph in the MRINFO format."
    print
    print "  - plot[:FILENAME]"
    print "      Plot a pre-computed graph. Plotting is done using the cairo library"
    print "      with the Fruchterman-Reingold layout algorithm. An optional FILENAME"
    print "      can be provided. The FILENAME extension specifies the output format."
    print "      Available formats are PNG, PDF ans SVG."
    print
    print "  - save:FILENAME:FORMAT"
    print "      Save a pre-computed graph into a file."
    print
    print "      FILENAME: name of the output file"
    print "      FORMAT  : file format (dot, graphml, graphmlz, edgelist)"
    print
    print "  - toy"
    print "      Generates a toy bipartite graph used for demo/debugging."
    print
    return


# -----[ header ]----------------------------------------------------
# Display program purpose, copyright, license and version
# -------------------------------------------------------------------
def header():
    print "Pareto-based random bipartite graph generation"
    print "(c) 2011, B. Quoitin, University of Mons, Belgium"
    print "This program is released under the LGPL license"
    print "Version: 0.1"
    print "Note: this program heavily relies on 'igraph'"
    print
    return
             

# -------------------------------------------------------------------
# This class holds the paramaters required to generate a random
# degree sequence, based on a Pareto distribution.
# -------------------------------------------------------------------
class DegreeSeqParams:

    def __init__(self, n, alpha, beta):
        self.__n= n
        self.__alpha= alpha
        self.__beta= beta

    def get_alpha(self):
        return self.__alpha

    def get_beta(self):
        return self.__beta

    def get_n(self):
        return self.__n

    def num_undefined(self):
        n= 0
        if (self.__n < 0): n+= 1
        if (self.__alpha < 0): n+= 1
        if (self.__beta < 0): n+= 1
        return n

    def solve_undefined(self, other):
        if (self.__n < 0):
            alpha2= other.get_alpha()
            beta2= other.get_beta()
            n2= other.get_n()
            self.__n= int((1.0 * alpha2) / self.__alpha \
                          * (1.0 * beta2) / self.__beta \
                          * n2 \
                          * (self.__alpha - 1.0) / (alpha2 - 1.0))
                      
        elif (self.__alpha < 0):
            n2= other.get_n()
            alpha2= other.get_alpha()
            beta2= other.get_beta()
            self.__alpha= (1.0 * alpha2) \
                          /(alpha2 - ((1.0 * self.__n) / n2) \
                            * (self.__beta/beta2) * (alpha2 - 1.0))

        elif (self.__beta < 0):
            alpha2= other.get_alpha()
            beta2= other.get_beta()
            n2= other.get_n()
            self.__beta= (1.0 * alpha2) / self.__alpha \
                         * (1.0 * n2) / self.__n \
                         * beta2 \
                         * (self.__alpha - 1.0) / (alpha2 - 1.0)

        return

    def exp_tot_degree(self):
        return self.__n * (self.__alpha * self.__beta)/(self.__alpha - 1)

    def dump(self):
        print "    number of nodes (N) = %d" % (self.__n)
        print "    exponent (A)        =",
        if (self.__alpha > 0):
            print "%.20f" % (self.__alpha)
        else:
            print "undefined"
        print "    scale (B)           =",
        if (self.__beta > 0):
            print "%.20f" % (self.__beta)
        else:
            print "undefined"
        return


# -----[ main ]-----------------------------------------------------
# This is where everything starts...
# -------------------------------------------------------------------
def main():
    global verbosity
    g= None

    header()

    if len(sys.argv) <= 1:
        usage()
        sys.exit(0)

    # Execute each graph transformations/operations requested by the
    # used on the command-line.
    for op in sys.argv[1:]:
        op_fields= op.split(":")
        op= op_fields[0]
        
        found= False
        for sop in operations.keys():
            if sop == op[0:len(sop)]:
                ndashes= ''.join(['-' for i in range(79-6-len(sop))])
                print "=[ %s ]=%s" % (sop.upper(), ndashes)
                func= operations[sop][0]
                min_args= operations[sop][1][0]
                max_args= operations[sop][1][1]
                if (len(op_fields[1:]) < min_args):
                    error("operation \"%s\" requires %d argument(s)" % \
                          (sop, min_args))
                elif (len(op_fields[1:]) > max_args):
                    error("operation \"%s\" takes max. %d argument(s)" % (sop, max_args))
                g= func(g, op_fields[1:])
                found= True
                break
        if not(found):
            error("unknown operation \"%s\"" % (op))
        print
                
    return


if __name__ == "__main__":
    import sys
    main()

# Clustering with wsClustering

This is an R package dedicated to clustering documents in an automated, fast and consistent way. This is an unsupervised way of clustering documents, which means that the topics will be generated from the most frequent words of the clusters, so no predefined topics are needed.

## Details

### Inputs

An excel file which contains a column with the full texts (which will be clustered).

### Optimal Number of Clusters

The optimal number of clusters is decided automatically within the `make_clusters` function. The function will test clusters up to a size of 50 to determine the optimal size. After the optimal number of clusters has been decided, optimal + 10 clusters will be created and also (optimal + 10) * 2. This is so it is as consistent as possible with how QUID outputs results. For each one of the clusters, the 4 most frequent words will be output as well.

### Unclustered Documents

The model is likely to be unable to cluster some of the texts provided. These will be specified as unclustered. The reason these could not be clustered is because they didn't contain enough meaningful words in order to end up in a cluster. However, these can still be treated as a cluster of their own.

### Output

A csv file with the original data, plus 7 more columns:

* Unclustered: Specifies the unclustered texts
* Cluster1: Optimal Clusters
* Words1: Frequent words for Cluster1
* Cluster2: Optimal + 10 Clusters
* Words2: Frequent words for Cluster2
* Cluster3: (Optimal + 10) * 2 Clusters
* Words3: Frequent words for Cluster3

## Installation

To install wsClustering you need to have the `devtools` package installed. To install devtools type in your console: 

```R
install.packages('devtools')
```

Then to install wsClustering run the following on your console:

```R
devtools::install_github('')
```

## Example

To use the package, you need to load it first, so type the following on the RStudio console:

```R
library(wsClustering)
```

Then in order to run the clustering process, you just use the `make_clusters` function.

It requires 3 arguments:

* file: The full path to the excel file containing the texts.
* skip: The number of rows in the excel file to skip. Useful when the columns do not start at the beginning of the file. The column headers should be included, so don't skip them.
* colname: The name of the column that contains the full texts. Remember R is case sensitive.

Usage:

```R
#this is an actual example you can run, but it will take about 30 mins, so be careful.
make_clusters(file = 'G:/ANALYTICS/DATA SCIENCE/text_clustering/inputs/orig/2011214605_Unilever+-+Shampoo.xlsx', 
              skip = 6,
              colname = 'Full Text')
```

The output will be placed in the same folder the input file was.

## Bugs or Features

If you find any bugs / errors / problems or have any suggestions for improvements please file them on the github issues page at:

www.github.com/wsClustering

or please contact the developer of the package directly at TBoutaris@webershandwick.com

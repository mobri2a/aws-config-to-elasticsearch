Import your AWS Config Snapshots into ElasticSearch
===================================================

### Author: Vladimir Budilov

-   [LinkedIn](https://www.linkedin.com/in/vbudilov/)

-   [Medium](https://medium.com/@budilov)

### What problem does this app solve?

You have a lot of resources in your AWS account and want to search and visualize
them. For example, you'd like to know your EC2 Avaiability Zone distribution or
how many EC2 instances are uzing a particular Security Group

### What does this app do?

It will ingest your AWS Config Snapshots into ElasticSearch for further analysis
with Kibana. Please refer to [this blog
post](https://aws.amazon.com/blogs/developer/how-to-analyze-aws-config-snapshots-with-elasticsearch-and-kibana/)
for a more in-depth explanation of this solution.

### Getting the code

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
git clone --depth 1 git@github.com:awslabs/aws-config-to-elasticsearch.git
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### The code

#### Prerequisites

-   AWS Config configured in one or more regions

-   Python 2.7 or 3.6

-   An ELK stack, up and running

-   Install the required packages. The requirements.txt file is included with
    this repo.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pip install -r ./requirements.txt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#### The command

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
./esingest.py
usage: esingest.py [-h] [--region REGION [--snapshotid]] --destination DESTINATION [--verbose]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  Let's say that you have your ElasticSearch node running on localhost:9200
    and you want to import only your us-east-1 snapshot, then you'd run the
    following command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
./esingest.py -d localhost:9200 -r us-east-1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  If you want to import Snapshots from all of your AWS Config-enabled regions,
    run the command without the '-r' parameter:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
./esingest.py -d localhost:9200
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  To run the command in verbose mode, use the -v parameter

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
./esingest.py -v -d localhost:9200 -r us-east-1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  To run the command against an existing snapshot, use the -s parameter with
    the -r parameter

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
./esingest.py --region us-east-1 --snapshotid 43499c03-c911-4ace-94f8-f36f38f1ff2d --verbose -d localhost:9200
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### Cleanup

\#\#\#\#DON'T RUN THESE COMMANDS IF YOU DON'T WANT TO LOSE EVERYTHING IN YOUR
ELASTICSEARCH NODE!

\#\#\#\#\#*THIS COMMAND WILL ERASE EVERYTHING FROM YOUR ES NODE --- BE CAREFUL
BEFORE RUNNING*

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
curl -XDELETE localhost:9200/_all
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to avoid losing all of your data, you can just iterate over all of your
indexes and delete them that way. The below command will print out all of your
indexes that contain 'aws::'. You can then run a DELETE on just these indexes.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
curl 'localhost:9200/_cat/indices' | awk '{print $3}' | grep "aws::"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Also delete the template which allows for creationg of a 'raw' string value
alongside every 'analyzed' one

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
curl -XDELETE localhost:9200/_template/configservice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

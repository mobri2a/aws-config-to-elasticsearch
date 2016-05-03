#!/usr/bin/env python

import datetime
import gzip
import json
import logging
import sys
import time
from argparse import ArgumentParser

import boto3
from botocore.client import Config

import elastic
from configservice_util import ConfigServiceUtil

DOWNLOADED_SNAPSHOT_FILE_NAME = "/tmp/configsnapshot" + \
                                str(time.time()) + ".json.gz"

REGIONS = [
    'us-west-1', 'us-west-2', 'eu-west-1', 'us-east-1',
    'eu-central-1', 'ap-southeast-1', 'ap-northeast-1',
    'ap-southeast-2', 'ap-northeast-2', 'sa-east-1']


def get_configuration_snapshot_file(s3conn, bucket_name, file_partial_name):
    """
    Returns the name of the configuration file from S3

    Loop through the files and find the current snapshot. Since s3 doesn't support regex lookups, I need to
    iterate over all of the items (and the config snapshot's name is not fully predictable because of the date value
    """
    result = None
    bucket = s3conn.Bucket(str(bucket_name))

    for key in bucket.objects.all():
        # logging.info("found: " + key.key)
        if file_partial_name in key.key:
            result = key.key
            verbose_log.info("Found the file in S3: " + result)

    return result


def load_data_into_es(filename, iso_now_time, es):
    data = None
    with gzip.open(filename, 'rb') as dataFile:
        if dataFile is not None:
            data = json.load(dataFile)

    itemcount = 0
    couldnotaddcount = 0

    if data is not None:
        configuration_items = data.get("configurationItems")

        if configuration_items is not None and len(configuration_items) > 0:
            for item in configuration_items:
                try:
                    indexname = item.get("resourceType").lower()
                    typename = item.get("awsRegion").lower()

                    verbose_log.info(
                        "storing in ES: " + str(item.get("resourceType")))
                    item['snapshotTimeIso'] = iso_now_time
                    response = es.add(
                        index_name=indexname,
                        doc_type=typename,
                        json_message=item)
                    if response is not None:
                        itemcount = itemcount + 1
                    else:
                        couldnotaddcount = couldnotaddcount + 1
                except:
                    app_log.error("Couldn't add item: " + str(
                        item) + " because " + str(sys.exc_info()))
                    pass

    return itemcount, couldnotaddcount

def loop_through_regions(my_regions, iso_now_time, es):

    for curRegion in my_regions:
        app_log.info("Current region: " + curRegion)

        s3conn = boto3.resource(
            's3',
            region_name=curRegion,
            config=Config(signature_version='s3v4'))

        if args.verbose:
            configlog = verbose_log
        else:
            configlog = None

        configService = ConfigServiceUtil(
            region=curRegion,
            verbose_log=configlog)

        bucket_name = configService.get_bucket_name_from_config_delivery_channel()
        if bucket_name is None:
            app_log.error(
                "The S3 bucket couldn't be found -- most likely you don't have AWS Config setup in this region")
            continue
        verbose_log.info(
            "Using the following bucket name to search for the snapshot: " + str(bucket_name))

        verbose_log.info("Creating snapshot")
        snapshotid = configService.deliver_snapshot()
        verbose_log.info("Got a new snapshot with an id of " + str(snapshotid))
        if snapshotid is None:
            app_log.info(
                "AWS Config isn't setup or your requests are being throttled")
            continue

        snapshot_file_path = get_configuration_snapshot_file(
            s3conn, bucket_name, snapshotid)
        if snapshot_file_path is None:
            for counter in xrange(1, 20):
                app_log.info(
                    " " + str(counter) + " - Waiting for the snapshot to appear")
                time.sleep(5)
                snapshot_file_path = get_configuration_snapshot_file(
                    s3conn, bucket_name, snapshotid)
                if snapshot_file_path is not None:
                    break

        if snapshot_file_path is None:
            app_log.error("Snapshot file is empty -- cannot proceed")
            continue

        app_log.info("Snapshot File Name: " + str(snapshot_file_path))

        verbose_log.info(
            "Downloading the file to " + str(
                DOWNLOADED_SNAPSHOT_FILE_NAME))
        s3conn.meta.client.download_file(
            bucket_name,
            snapshot_file_path,
            DOWNLOADED_SNAPSHOT_FILE_NAME)

        verbose_log.info("Loading the file into elasticsearch")
        itemCount, couldNotAdd = load_data_into_es(DOWNLOADED_SNAPSHOT_FILE_NAME, iso_now_time, es)

        if itemCount > 0:
            app_log.info("Added: " + str(itemCount) +
                         " items into ElasticSearch from " + curRegion)
        if couldNotAdd > 0:
            app_log.warn("Couldn't add " + str(couldNotAdd) +
                         " to ElasticSearch. Maybe you have permission issues? ")


def main(args, es):
    iso_now_time = datetime.datetime.now().isoformat()
    app_log.info("Snapshot Time: " + str(iso_now_time))

    region = args.region

    # This call is light, so it's ok not to check whether the template already
    # exists
    es.set_not_analyzed_template()

    my_regions = []
    if region is not None:
        my_regions.append(region)
    else:
        my_regions = REGIONS

    verbose_log.info("Looping through the regions")

    loop_through_regions(my_regions, iso_now_time, es)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--region', '-r',
                        help='The region that needs to be analyzed. If left blank all regions will be analyzed.')
    parser.add_argument('--destination', '-d', required=True,
                        help='The ip:port of the elastic search instance')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help='If selected, the app runs in verbose mode -- a lot more logs!')
    args = parser.parse_args()

    logging.basicConfig(format=' %(name)-12s:  %(message)s')

    # Setup the main app logger
    app_log = logging.getLogger("app")
    app_log.setLevel(level=logging.INFO)

    # Setup the verbose logger
    verbose_log = logging.getLogger("verbose")
    if args.verbose:
        verbose_log.setLevel(level=logging.INFO)
    else:
        verbose_log.setLevel(level=logging.FATAL)

    # Mute all other loggers
    logging.getLogger("root").setLevel(level=logging.FATAL)
    logging.getLogger("botocore.credentials").setLevel(level=logging.FATAL)
    logging.getLogger(
        "botocore.vendored.requests.packages.urllib3.connectionpool").setLevel(
        level=logging.FATAL)
    logging.getLogger("boto3").setLevel(level=logging.FATAL)
    logging.getLogger("requests").setLevel(level=logging.FATAL)

    destination = None
    if args.destination is None:
        app_log.error("You need to enter the IP of your ElasticSearch instance")
        exit()

    destination = "http://" + args.destination

    verbose_log.info("Setting up the elasticsearch instance")

    main(args, elastic.ElasticSearch(connections=destination, log=verbose_log))
#!/usr/bin/env python3

import argparse
import copy
import datetime
import json
import logging
import os
import uuid


class Entity():

    def __init__(self):
        self._data = None
        self._filename = None

    def __repr__(self):
        return f"<Entity({self._filename})>"

    @property
    def filename(self):
        return self._filename

    @property
    def id(self):
        return self._data["id"]

    @property
    def type(self):
        return self._data["type"]

    @property
    def title(self):
        return self._data["attributes"]["title"]

    @title.setter
    def title(self, value):
        self._data["attributes"]["title"] = value

        # No idea on why we have two title fields, so lets also change
        # in attributes :-/
        a = self.attributes
        if "visState" in a and "title" in a["visState"]:
            a["visState"]["title"] = value
            self.attributes = a

    @property
    def size(self):
        return len(json.dumps(self._data))

    @property
    def attributes(self):
        a = self._data["attributes"]

        if "searchSourceJSON" in a["kibanaSavedObjectMeta"]:
            a["kibanaSavedObjectMeta"]["searchSourceJSON"] = json.loads(a["kibanaSavedObjectMeta"]["searchSourceJSON"])
        if "visState" in a:
            a["visState"] = json.loads(a["visState"])

        return a

    @attributes.setter
    def attributes(self, value):
        if "searchSourceJSON" in value["kibanaSavedObjectMeta"]:
            value["kibanaSavedObjectMeta"]["searchSourceJSON"] = json.dumps(value["kibanaSavedObjectMeta"]["searchSourceJSON"])
        if "visState" in value:
            value["visState"] = json.dumps(value["visState"])

        self._data["attributes"] = value

    @staticmethod
    def load_from_data(data):
        """
        Return Entity class instance created from given data.
        """
        assert "id" in data
        assert "type" in data
        assert "attributes" in data

        e = Entity()

        e._data = data
        e._filename = f"{e.type}_{e.id}.json"

        return e

    @staticmethod
    def load_from_scm(filename):
        """
        Return Entity class instance from given filename.
        """
        e = Entity()

        with open(filename, 'r') as fp:
            data = json.load(fp)

        assert len(data) == 1
        assert "id" in data[0]
        assert "type" in data[0]
        assert "attributes" in data[0]

        e._data = data[0]
        e._filename = filename

        return e

    @staticmethod
    def load_all_from_scm(dirname):
        """
        Return Entity class instance from every suitable file in given directory.
        """
        data = []

        for f in os.listdir(dirname):
            if f.endswith(".json"):
                data.append(Entity.load_from_scm(f))

        return data

    def duplicate(self):
        """
        Create copy of this entity with new ID.
        """
        e = Entity()

        e._data = copy.deepcopy(self._data)
        e._data["id"] = str(uuid.uuid4())
        e._data["updated_at"] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        e._filename = f"{e.type}_{e.id}.json"

        return e

    def dump_to_scm(self, filename=None):
        """
        Save pretty formatted entity to filename.
        """
        if filename is None:
            filename = self._filename

        with open(filename, "w") as fp:
            json.dump([self._data], fp, sort_keys=True, indent=4, separators=(',', ': '))

    def dumps_to_oneline(self):
        """
        Dump to one line json suitable to be written to ndjson.
        """
        return json.dumps([self._data])


def fix_title(args):
    for entity in Entity.load_all_from_scm(args.dirname):
        if entity.type not in ("visualization", "dashboard"):
            print(f"Skipping {entity} as it has unsupported type")
            continue

        title_old = entity.title
        title_new = title_old.strip()
        if title_new.startswith("sat "):
            title_new = title_new.replace("sat ", "Sat ", 1)
        print(f"{entity.filename}: {title_old} => {title_new}")
        entity.title = title_new

        entity.dump_to_scm()


def dump_to_ndjson(args):
    with open(args.filename, 'w') as fp:
        for entity in Entity.load_all_from_scm("."):
            fp.write(entity.dumps_to_oneline() + "\n")


def duplicate_selected(args):
    for entity in Entity.load_all_from_scm("."):
        if entity.type != 'visualization' or not entity.title.startswith("Sat 6.9 "):
            continue

        new = entity.duplicate()
        print(f"Duplicating {entity} to {new}")

        new.title = new.title.replace("Sat 6.9 ", "Sat 6.10 ", 1)

        a = new.attributes

        # Changing filters is hard. I have no idea on why it is on
        # two places. Variable new.attributes now look like this:
        #
        #     {'description': '',
        #      'kibanaSavedObjectMeta': {'searchSourceJSON': {'filter': [{'$state': {'store': 'appState'},
        #                                                                 'meta': {'alias': None,
        #                                                                          'disabled': False,
        #                                                                          'indexRefName': 'kibanaSavedObjectMeta.searchSourceJSON.filter[0].meta.index',
        #                                                                          'key': 'name',
        #                                                                          'negate': False,
        #                                                                          'params': {'query': 'Misc_simple_tests/60-generate-applicability',
        #                                                                                     'type': 'phrase'},
        #                                                                          'type': 'phrase',
        #                                                                          'value': 'Misc_simple_tests/60-generate-applicability'},
        #                                                                 'query': {'match': {'name': {'query': 'Misc_simple_tests/60-generate-applicability',
        #                                                                                              'type': 'phrase'}}}},
        #                                                                {'$state': {'store': 'appState'},
        #                                                                 'meta': {'alias': None,
        #                                                                          'disabled': False,
        #                                                                          'indexRefName': 'kibanaSavedObjectMeta.searchSourceJSON.filter[1].meta.index',
        #                                                                          'key': 'query',
        #                                                                          'negate': False,
        #                                                                          'type': 'custom',
        #                                                                          'value': '{"wildcard":{"parameters.version.keyword":"*-6.9.*"}}'},
        #                                                                 'query': {'wildcard': {'parameters.version.keyword': '*-6.9.*'}}}],
        #                                                     'indexRefName': 'kibanaSavedObjectMeta.searchSourceJSON.index',
        #                                                     'query': {'language': 'lucene',
        #                                                               'query': ''}}},
        #      'title': 'Sat 6.10 generate-applicability',
        #     [...]

        for f in a["kibanaSavedObjectMeta"]["searchSourceJSON"]["filter"]:
            if "query" in f \
               and "wildcard" in f["query"] \
               and "parameters.version.keyword" in f["query"]["wildcard"]:
                old_kw = f["query"]["wildcard"]["parameters.version.keyword"]
                new_kw = "*-6.10.*"
                print(f"    changing attributes.kibanaSavedObjectMeta.filter[].query.wildcard from {old_kw} to {new_kw}")
                f["query"]["wildcard"]["parameters.version.keyword"] = new_kw

                old_kw = f["meta"]["value"]
                new_kw = old_kw.replace("*-6.9.*", "*-6.10.*", 1)
                print(f"    changing attributes.kibanaSavedObjectMeta.filter[].meta.value from {old_kw} to {new_kw}")
                f["meta"]["value"] = new_kw

        new.attributes = a

        new.dump_to_scm()


def split_export(args):
    with open(args.filename, 'r') as export_fp:
        for row in export_fp:
            entity_raw = json.loads(row)
            if 'exportedCount' in entity_raw:
                pass   # this is just summary of the export like '{"exportedCount": 41, "missingRefCount": 0, "missingReferences": []}'
            elif 'type' in entity_raw and 'id' in entity_raw:
                Entity.load_from_data(entity_raw).dump_to_scm()
            else:
                raise Exception(f"Unknown document: {entity_raw}")


def list_objects(args):
    for e in Entity.load_all_from_scm("."):
        print(f"e.filename: {e.type} '{e.title}' {e.size} B")


def main():
    parser = argparse.ArgumentParser(prog="Work with Kibana saved objects")
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="debug output")
    subparsers = parser.add_subparsers(
        dest="subcommand", title="subcommands",
        description="Commands to choose from",
        help="use `<subcommand> --help` for more info")

    parser_a = subparsers.add_parser(
        "fix_title",
        help="fix title of the stored saved objects, please edit code for actual changing the title")
    parser_a.add_argument(
        "--dirname", default=".",
        help="directory with stored objects JSONs")

    parser_b = subparsers.add_parser(
        "dump_to_ndjson",
        help="dump all stored saved JSONs into one NDJSON file which can be imported into Kibana")
    parser_b.add_argument(
        "--filename", default="import.ndjson",
        help="filename where to dump the data")

    parser_c = subparsers.add_parser(
        "duplicate_selected",
        help="duplicate visualizations and change filters, please edit code for actual changes")

    parser_d = subparsers.add_parser(
        "split_export",
        help="split exported NDJSON file to individual JSONs we can store in git")
    parser_d.add_argument(
        "--filename", default="export.ndjson",
        help="filename with export from Kibana")

    parser_e = subparsers.add_parser(
        "list_objects",
        help="list JSONs and titles in them")

    args = parser.parse_args()

    logger = logging.getLogger("kibana_objects_tool")
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler_stream = logging.StreamHandler()
    handler_stream.setFormatter(formatter)
    handler_stream.setLevel(logging.DEBUG if args.debug else logging.WARNING)
    logger.addHandler(handler_stream)
    handler_file = logging.FileHandler("/tmp/kibana_objects_tool.log")
    handler_file.setLevel(logging.DEBUG)
    handler_file.setFormatter(formatter)
    logger.addHandler(handler_file)

    logging.debug(f"Args: {args}")

    if args.subcommand == "fix_title":
        fix_title(args)
    elif args.subcommand == "dump_to_ndjson":
        dump_to_ndjson(args)
    elif args.subcommand == "duplicate_selected":
        duplicate_selected(args)
    elif args.subcommand == "split_export":
        split_export(args)
    elif args.subcommand == "list_objects":
        list_objects(args)
    else:
        raise Exception(f"Unknown subcommand {args.subcommand}")

if __name__ == "__main__":
    main()

Manage Kibana saved objects in git
==================================

This tool is supposed to help manage Kibana saved objects in git.

Make sure you are in a directopry where your saved object JSONs reside
when running this script.

Backup from Kibana
------------------

If you want to prapare what you have in Kibana for storing in code repository,
first get the `export.ndjson` export file from Kibana UI:

    Kibana -> Stack Management -> Saved Objects -> fileter for objects you are interested in -> Export X objects

And then to use the tool to prepare for a commit:

    $ ./kibana_objects_tool.py split_export --filename export.ndjson
    $ rm export.ndjson
    $ git add *.json
    $ git diff
    $ git commit -m "New version of Kibana saved objects"

Now you have these saved objects in individual files (one saved object for
one file), keys inside of the JSONs are ordered and JSONs itself are nicely
indented.

Restore to Kibana
-----------------

To be able to import to Kibana, we need to join all JSONs into one NDJSON
file which can be imported into Kibana:

    $ ./kibana_objects_tool.py dump_to_ndjson --filename import.ndjson

Then you can upload it in:

    Kibana -> Stack Management -> Saved Objects -> Import

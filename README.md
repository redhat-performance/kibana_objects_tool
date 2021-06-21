Manage Kibana saved objects in git
==================================

This tool is supposed to help manage Kibana saved objects in git.

E.g. if you want to reorder and split what you have in Kibana, first
get the `export.ndjson` export file from Kibana UI:

    Kibana -> Stack Management -> Saved Objects -> fileter for objects you are interested in -> Export X objects

And then to use the tool to prepare for a commit:

    $ ./kibana_objects_tool.py split_export --filename export.ndjson
    $ rm export.ndjson
    $ git add *.json
    $ git diff
    $ git commit -m "New version of Kibana saved objects"

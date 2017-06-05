curl -XPOST  http://$1:$2/_aliases -d '{"actions" : [{ "add" : { "index" : "'$3'", "alias" : "'$4'" } }]}'
if [ $# -eq 5 ]
  then
    curl -XPOST  http://$1:$2/_aliases -d '{"actions" : [{ "remove" : { "index" : "'$5'", "alias" : "'$4'" } }]}'
fi
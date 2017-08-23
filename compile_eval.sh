TIMESTAMP=$1
for f in eval/${TIMESTAMP}/* ;
do
	cat $f | jq -c .[] >> eval/${TIMESTAMP}.out
done
jq -c -s . eval/${TIMESTAMP}.out > eval/${TIMESTAMP}.out.compiled
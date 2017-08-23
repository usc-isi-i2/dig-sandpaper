TIMESTAMP=`date "+%Y-%m-%d-%H-%M-%S"`
mkdir eval/${TIMESTAMP}
for f in eval/*.json ;
do
	bin/query.sh -q $f > eval/$TIMESTAMP/$(basename ${f}).out
done

./compile_eval.sh $TIMESTAMP
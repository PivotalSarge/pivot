#!/bin/sh

#echo $0 "$@"

if [ 1 -lt $# ]
then
  EXTENSION=`echo $2 | sed -e 's/.*\(\.[^.]*\)/\1/'`
  if [ ".bin" = "$EXTENSION" ]
  then
    cat /dev/null >$2
    echo "DEADBEEF" >>$2
  elif [ ".json" = "$EXTENSION" ]
  then
    cat /dev/null >$2
    echo "{" >>$2
    echo "  \"type\": \"PING\"" >>$2
    echo "}" >>$2
  fi
fi

exit 0

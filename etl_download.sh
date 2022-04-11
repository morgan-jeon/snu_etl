cd /home/ahrjskr/python/snu_etl/
python3 -u ETL_Download.py
/usr/bin/rclone copy --update --verbose --transfers 30 --checkers 8 --contimeout 60s --timeout 300s --retries 3 --low-level-retries 10 --stats 1s "/home/ahrjskr/python/snu_etl/vod" "onedrive:Documents/"
rm /home/ahrjskr/python/snu_etl/vod/*

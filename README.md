# SubScrubber
Cleans weird spaces (Â, NBSP, zero-width) and mojibake (â€™) from SRT files.


### Usage
Clean one SRT, writes new .clean.srt file
```
python subscrub.py /path/to/file.srt
```

Clean every SRT in a folder (recursively), writing new .clean.srt files
```
python subscrub.py /path/to/folder
```


### Options   
--in-place &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Overwrite original files    
--backup &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; When --in-place is used, keeps original as .bak 
--utf8-bom &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Write UTF-8 with BOM (helps some older players)   
--quiet &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Less console output


### License
Copyleft 20205, no rights reserved.  Do what you will with this vibeslop.

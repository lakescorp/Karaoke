# Karaoke
 An app to sing karoke with you own library in a new way.

## Main objective
The main objective of the app is to make karaoke singing easier for the singer.

This is achieved by playing the original song for the singer through the headphones while only the instrumental is heard through the speakers.

## How to set up
In the directory there is a file called .env in which you must change the path to where your files are located.

The variable that has to be changed is **DATA_PATH**

## How to set up files
In the assigned folder there must be a file in JSON format with the following structure:

```
{
    "title":"God's Plan",
    "artist":"Drake",
    "songpath":"C:\\Users\\grmap\\Music\\Karaoke\\Drake - God's Plan\\song.wav",
    "karaokepath":"C:\\Users\\grmap\\Music\\Karaoke\\Drake - God's Plan\\instrumental.wav",
    "lyricspath":"C:\\Users\\grmap\\Music\\Karaoke\\Drake - God's Plan\\lyrics.lrc"
}
```
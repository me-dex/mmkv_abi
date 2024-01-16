# mmkv_abi

A Python library for MakeMKV via the makemkvcon ABI. Based upon the open source makemkvgui
implementation.

This project is still a work-in-progress and does not contain full functionality. It will be
updated as free time allows.

## Why not just use makemkvcon?

makemkvcon is a great way to utilize MakeMKV via the commandline and for creating simple scripts
for automating disc ripping. However, its limitations start to show when trying to extract more
specific details about a drive/disc or customizing a rip operation. mmkv_abi enables more
information and finer controls over what is extracted from a disc.

## Example

Included in this repo is an example script which can help automate the ripping of TV shows by
scanning a disc for titles which are greater than 20 minutes and less than 50 minutes. This is
only a small example of the type of logic that can be created for faster ripping operations.

## License

mmkv_abi is licensed under GPL 3.0 as a way to ensure that open source continues to thrive.

> Human knowledge belongs to the world.
>
> — Milo Hoffman (Antitrust)

This repo contains branches with minimal working examples for submission to the [VLINCS Leaderboard](https://pages.nist.gov/vlincs/).

To see an example for a given round, clone this repository, then check out the corresponding branch.

For example

```
git clone https://github.com/usnistgov/vlincs-example.git
cd vlincs-example
git checkout self-test-ta1
```

The available branches are

* https://github.com/usnistgov/vlincs-example/tree/self-test-ta1

### System Output Format for Re-identification (ReID) and Geo Location (GeoLoc) Tasks

All objects re-identified by the system for a given input video file should be in the same system output file. If there is no output for a given input video, it means no output from the ReID system. 

Due to the data volume, each system output file must be stored as a Parquet file to facilitate efficient storage and retrieval. Parquet stores data in a columnar format. Both the ReID and GeoLoc tasks use the same system output format. However, the scorer will ignore the last three columns for the ReID task. Table 1 lists the columns defined for the system output:

| Column Name | Description | Valid Range | Unit |
| ----- | :---- | :---- | :---- |
| frame\_id | A number representing the unique frame number in which the object appears | int \>= 0 | n/a |
| object\_id | A number representing the unique identifier of the predicted object | int \>= 0 | n/a |
| x | A number representing the x-coordinate of the top-left point of the bounding box in pixels | 0\<= int \<= frame\_width | pixel |
| y | A number representing the y-coordinate of the top-left point of the bounding box in pixels | 0\<= int \<= frame\_height | pixel |
| w | A number representing the width of the bounding box in pixels | 0\<= int \<= (frame\_width \- x) | pixel |
| h | A number representing the height of the bounding box in pixels | 0\<= int \<= (frame\_height \- y) | pixel |
| conf | A number between 0 and 1 representing the level of certainty in the prediction, with 0 as complete uncertainty and 1 as absolute certainty. | 0\<= float \<= 1.0 | n/a |
| class\_id | A number denoting the class of the object: 1 for a person 2 for a vehicle 3 for a generic object that is neither a person nor a vehicle | int \>= 0 | n/a |
| lat | A decimal number indicating how far a location is from the equator, ranging from \-90° to 90°, with 0° at the equator, a positive value being North of the equator, and a negative value being South of the equator. The value is for the Universal Transverse Mercator (UTM) map projection system. | \-90 \<= double \<= 90 | degree |
| long | A decimal number indicating how far a location is from the Prime Meridian, ranging from \-180° to 180°, with 0° at the Prime Meridian, a positive value being East of the Prime Meridian and a negative value being West of the Prime Meridian. The value is for the Universal Transverse Mercator (UTM) map projection system  | \-180 \<= double \<= 180 | degree |
| alt | A number indicating the altitude in meters of an object in reference to sea level, with a negative value as below sea level and a positive value as above sea level | float | meter |

Table 1: System Output Format

Because Parquet is a binary format, performers must use a tool or library to encode and decode the output into Parquet.

### Self-Test Submission Protocol

Performers must create their own Google Drive account from which they will submit their system output. Before making the first submission, they must register their Google Drive account with NIST. Performers can make submissions once NIST has added their Google Drive account. 

Below are the steps. Steps 1-2 are only done once for the duration of the program:

1. Create a Google Drive account (from which a performer will use to submit his system output). It is recommended that this drive be ‘My Drive’, not a ‘Shared drive’ because some organizations do not allow sharing a file on their institutional shared drive with an account not on the shared drive.  
2. Register the Google Drive account with NIST by emailing [vlincs@nist.gov](mailto:vlincs@nist.gov) with the following requested information:  
   * Team name (alphanumeric, no special characters, no spaces) \-  the performer may be asked to change their team name if it collides with another team.  
   * Google Drive account email   
   * Point of contact email address (the performer’s official institutional email)  
3. Zip up the system output.  
   * We should see a list of system output files when the zip file is uncompressed. There should be no directory or subdirectory.  
   * For example: <code>zip MyBestSys.zip \*.parquet   </code>
4. Rename the zip file to:   
   \<Leaderboard Name\>\_\<Dataset Name\>\_\<Submission Name\>.zip  
   where  
   \<Leaderboard Name\> can be one of  
* <code>self-test-ta1  </code>
* ... (we will add as we get more leaderboards)  
  \<Dataset Name\> can be one of  
* <code>meva-rev1   </code>
* <code>meva-rev2  </code>
* ... (we will add as we get more leaderboards)  
  \<Submission Name\> is an alpha-numeric, mnemonic name chosen by the performer  
  For example: <code>mv MyBestSys.zip self-test-ta1\_meva-rev2\_MyBestSys.zip   </code>
5. Upload the zip file to the performer’s Google Drive account.  
6. Share the zip file with [vlincs@nist.gov](mailto:vlincs@nist.gov).  
7. Unshare the zip file once Job Status is “None” to make another submission. To see the Job Status, go to the leaderboard [https://pages.nist.gov/vlincs/](https://pages.nist.gov/vlincs/). There is a Teams/Jobs table that lists the statuses of all the jobs. 

Performers are allowed to make one submission per month during the sef-test period. Please consult the evaluation schedule in the evaluation plan for the self-test period. Each submission will be scored with the results displayed to the leaderboard shortly thereafter.

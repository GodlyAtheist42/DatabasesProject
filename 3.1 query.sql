query = 'SELECT filepath, caption, photoPoster, photoID \
             FROM photo \
             WHERE (allFollowers = 1 AND photoPoster in (SELECT username_followed FROM follow WHERE username_follower = %s AND followStatus = 1)) \
             OR \
             (      photoID in (SELECT PhotoId \
				    FROM SharedWith \
					WHERE (groupName,groupOwner ) IN (SELECT groupName,owner_username \
                                                          FROM BelongTo \
					                                      WHERE member_username = %s)\
			))'
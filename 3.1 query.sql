SELECT filepath, caption, photoPoster, photoID 
FROM photo 
WHERE (allFollowers = 1 AND photoPoster in (SELECT username_followed FROM follow WHERE username_follower = 'nKundalia' AND followStatus = 1)) 
OR
(photoPoster IN (SELECT member_username
                FROM BelongTo as b
                WHERE member_username = 'nKundalia' AND
                 photoID in (SELECT PhotoId
								FROM SharedWith 
								WHERE groupName, owner_username IN (SELECT groupName, owner_username
								FROM BelongTo
								WHERE member_username = 'nKundalia')
                            )
                )
)
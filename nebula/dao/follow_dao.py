#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from nebula.dao.base_dao import BaseDao
from nebula.models import FollowKeywordModel as Model

logger = logging.getLogger("nebula.api.dao.follow_keyword")

class FollowKeywordDao(BaseDao):
    followed_limit = 200
    ignored_limit = 200

    def _get_follow_keyword(self, keyword, keyword_type):
        query = self.session.query(Model).filter(Model.keyword == keyword).filter(Model.keyword_type==keyword_type)
        return query.first()

    def get_follow_keyword_list(self, is_followed=False, is_ignored=False, keyword_type=None):
        # only filter any keyword_type followed list or ignored list, or all list.
        query = self.session.query(Model)
        if is_followed:
            query = query.filter(Model.is_followed == True)
        if is_ignored:
            query = query.filter(Model.is_ignored == True)
        if keyword_type:
            query = query.filter(Model.keyword_type == keyword_type)

        return [fk.to_dict() for fk in query.all()]

    def add_follow_keyword(self, follow_keyword):
        logger.debug("input follow keyword: %s", follow_keyword)
        k_type = follow_keyword['keyword_type']
        exist = self._get_follow_keyword(follow_keyword['keyword'], k_type)
        
        if not exist:
            logger.debug("add follow keyword.")
            if not follow_keyword.has_key("is_followed"):
                follow_keyword["is_followed"] = False
            if not follow_keyword.has_key("is_ignored"):
                follow_keyword["is_ignored"] = False
                
            fk = Model.from_dict(follow_keyword)
            if fk.is_followed and self.reach_follow_limit(k_type):
                return False, "关注关键字数量超过上限"
            if fk.is_ignored and self.reach_ignored_limit(k_type):
                return False, "忽略关键字数量超过上限"
            logger.debug("add follow keyword: %s", fk.to_dict())
            self.session.add(fk)
        else:
            # not update, just modify is_followed or is_ignored status.
            logger.debug("modify follow keyword.")
            logger.debug("exists: %s", exist.to_dict())
            if follow_keyword.has_key("is_followed"):
                if follow_keyword["is_followed"] and not exist.is_followed:
                    # turn is_followed on
                    if not self.reach_follow_limit(k_type):
                        exist.is_followed = True
                    else:
                        return False, "关注关键字数量超过上限"
                elif not follow_keyword["is_followed"] and exist.is_followed:
                    # turn is_followed off
                    exist.is_followed = False
            
            if follow_keyword.has_key("is_ignored"):
                if follow_keyword["is_ignored"] and not exist.is_ignored:
                    # turn is_ignored on
                    if not self.reach_ignored_limit(k_type):
                        exist.is_ignored = True
                    else:
                        return False, "忽略关键字数量超过上限"
                elif not follow_keyword["is_ignored"] and exist.is_ignored:
                    # turn is_ignored off
                    exist.is_ignored = False
            
            logger.debug("modified follow keyword: %s", exist.to_dict())
        self.session.commit()
        return True, None

    def delete_follow_keywords(self, follow_keywords, keyword_type):
        query = self.session.query(Model)
        query = query.filter(Model.keyword_type == keyword_type).filter(Model.keyword.in_(follow_keywords))
        query.delete(synchronize_session=False)
        self.session.commit()
        
    def clear(self):
        query = self.session.query(Model)
        query.delete(synchronize_session=False)
        self.session.commit()
        
    def reach_follow_limit(self, keyword_type):
        if self.get_follow_count(keyword_type) < self.followed_limit:
            return False
        return True
    
    def reach_ignored_limit(self, keyword_type):
        if self.get_ignored_count(keyword_type) < self.ignored_limit:
            return False
        return True
        
    def get_follow_count(self, keyword_type):
        return self.get_keyword_count(keyword_type, is_followed=True)
    
    def get_ignored_count(self, keyword_type):
        return self.get_keyword_count(keyword_type, is_ignored=True)
        
    def get_keyword_count(self, keyword_type, is_followed=False, is_ignored=False):
        query = self.session.query(Model)
        if is_followed:
            query = query.filter(Model.is_followed == True)
        if is_ignored:
            query = query.filter(Model.is_ignored == True)
        if keyword_type:
            query = query.filter(Model.keyword_type == keyword_type)
            
        return query.count()

    


#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, logging
import unittest

from sqlalchemy.orm import sessionmaker

from nebula.views import follow
from nebula.dao.follow_dao import FollowKeywordDao
from nebula.models import FollowKeywordModel as Model
from nebula.tests.base import WebTestCase, wsgi_safe, Auth_Code

logging.basicConfig(level=logging.DEBUG)

# global application scope.  create Session class, engine
Session = sessionmaker()

FollowKeywords = [
    {
        "keyword":"login",
        "keyword_type":"page",
        "is_followed":True,
        "is_ignored":False,
    }
]

@wsgi_safe
class TestFollowkeywordHandler(WebTestCase):
    url_prefix = "/platform/follow_keyword"
    url = "{}?auth={}".format(url_prefix, Auth_Code)
    
    def get_handlers(self):
        return [(TestFollowkeywordHandler.url_prefix, follow.FollowKeywordHandler)]

    @classmethod
    def setUpClass(cls):
        cls.dao = FollowKeywordDao()
        cls.dao.clear()

    def tearDown(self):
        self.dao.clear()

    def test_add_followkeyword(self):
        
        post_args = json.dumps(FollowKeywords)
        response = self.fetch(self.url, method='POST', body=post_args)
        print response
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.dao.get_follow_count("page"), 1)
        self.assertEqual(self.dao.get_ignored_count("page"), 0)
        self.dao.clear()

    def test_modify_follow(self):
        self.dao.add_follow_keyword(FollowKeywords[0])
        new = dict( (k,v) for k,v in FollowKeywords[0].iteritems())
        new["is_ignored"] = True
        new.pop("is_followed")
        post_args = json.dumps([new, ])
        # add ignored to exist follow keyword
        response = self.fetch(self.url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        f = self.dao._get_follow_keyword(new["keyword"], new["keyword_type"])
        self.assertEqual(f.is_followed, True)
        self.assertEqual(f.is_ignored, True)
        print("turn is_ignored on success!")
        
        # disable ignored
        new = dict( (k,v) for k,v in FollowKeywords[0].iteritems())
        new.pop("is_followed")
        post_args = json.dumps([new, ])
        response = self.fetch(self.url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        f = self.dao._get_follow_keyword(new["keyword"], new["keyword_type"])
        self.assertEqual(f.is_followed, True)
        self.assertEqual(f.is_ignored, False)
        print("turn is_ignored off success!")
        
        # disable follow
        new = dict( (k,v) for k,v in FollowKeywords[0].iteritems())
        new["is_followed"] = False
        post_args = json.dumps([new, ])
        response = self.fetch(self.url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        f = self.dao._get_follow_keyword(new["keyword"], new["keyword_type"])
        self.assertEqual(f.is_followed, False)
        self.assertEqual(f.is_ignored, False)
        print("turn is_follow off success!")
        self.dao.clear()

    def test_get_followkeyword(self):
        for fk in FollowKeywords:
            self.dao.add_follow_keyword(fk)

        response = self.fetch("%s&keyword_type=%s" % (self.url, FollowKeywords[0]['keyword_type']))
        res = json.loads(response.body)
        print res
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        print "return: %s" % res["values"]
        print "expect: %s" % FollowKeywords
        self.dao.clear()
#        self.assertEqual(len(res['values']), 1)
        
    def test_add_followkeyword_followed_reach_limit(self):
        import string, random
        seeds = list(string.ascii_letters)[:10]
        ks = set()
        for _ in xrange(500):
            random.shuffle(seeds)
            ks.add("".join(seeds))
            if len(ks) > 200:
                continue
        fks = list( dict(is_followed=True, keyword=k, keyword_type="page") for k in ks)
        try:
            for _ in fks[:200]:
                s, msg = self.dao.add_follow_keyword(_)
                assert s, msg
                
            s, msg = self.dao.add_follow_keyword(fks[200])
            assert not s
            assert msg == "关注关键字数量超过上限"
            # via api
            post_args = json.dumps([fks[200]])
            response = self.fetch(self.url, method='POST', body=post_args)
            print response
            res = json.loads(response.body)
            print res
            self.assertEqual(res['status'], 400)
            self.assertEqual(res['msg'].encode("utf8"), "当添加关键字: %s 时, 关注关键字数量超过上限" % fks[200]['keyword'])
        finally:
            self.dao.clear()

    def test_add_followkeyword_ignored_reach_limit(self):
        import string, random
        seeds = list(string.ascii_letters)[:10]
        ks = set()
        for _ in xrange(500):
            random.shuffle(seeds)
            ks.add("".join(seeds))
            if len(ks) > 200:
                continue
        fks = list( dict(is_ignored=True, keyword=k, keyword_type="page") for k in ks)
        try:
            for _ in fks[:200]:
                s, msg = self.dao.add_follow_keyword(_)
                assert s, msg
                
            s, msg = self.dao.add_follow_keyword(fks[200])
            assert not s
            assert msg == "忽略关键字数量超过上限"
            # via api
            post_args = json.dumps([fks[200]])
            response = self.fetch(self.url, method='POST', body=post_args)
            print response
            res = json.loads(response.body)
            print res
            self.assertEqual(res['status'], 400)
            self.assertEqual(res['msg'].encode("utf8"), "当添加关键字: %s 时, 忽略关键字数量超过上限" % fks[200]['keyword'])
        finally:
            self.dao.clear()
            
if __name__ == '__main__':
    unittest.main()
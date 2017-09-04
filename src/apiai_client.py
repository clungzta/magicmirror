# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import uuid
import json
import apiai
import pprint as pp

class ApiAIClient:
    def __init__(self, client_access_token, logging=1):
        self.ai = apiai.ApiAI(client_access_token)
        self.session_id = uuid.uuid4().hex # for user identification
        self.logging = logging    

        if self.logging:
            print('Beginning apapi session: {}'.format(self.session_id))

    def send_query(self, query_str, entities=None):
        request = self.ai.text_request()
        request.session_id = self.session_id
        request.entities = entities
        request.query = query_str
        
        if self.logging:
            print('Query text: {}'.format(request.query))

        response = request.getresponse()
        resp_dict = json.loads(response.read())['result']
        resp_dict.pop('score')

        if self.logging:
            print('Query response:')
            pp.pprint(resp_dict, width=160, indent=2)

        return resp_dict

    def send_entities_request(self, entities_dict):
        '''

        @entitites dict: key is the entitiy name, value is the list of entries for that entity

        '''

        user_entities = [apiai.UserEntity(entity_name, entries, self.session_id) for entity_name, entries in entities_dict.items()]
        user_entities_request = self.ai.user_entities_request(user_entities)
        user_entities_response = user_entities_request.getresponse()
        
        if self.logging:
            print('Upload user entities response: {}'.format(user_entities_response.read()))

        return user_entities_response

if __name__ == '__main__':
    ai = ApiAIClient('d700d2f861f3428e994fa7d4a094efb1')
    
    # user_entities_response = ai.send_entities_request({'person' : [apiai.UserEntityEntry('person', ['Alex'])]})
    print('\n')
    # response = ai.send_query("how are you?")
    response = ai.send_query("Hi Magic Mirror, my name is Alex")
    
    print('\n')    
    response = ai.send_query("What is my name?")

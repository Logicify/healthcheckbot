#    Healthcheck Bot
#    Copyright (C) 2018 Dmitry Berezovsky
#    
#    HealthcheckBot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    HealthcheckBot is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
from datetime import datetime

from decimal import Decimal
from psycopg2.extras import RealDictCursor

from healthcheckbot.common.model import WatcherModule, ParameterDef
import psycopg2


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)


class DatabaseQueryWatcher(WatcherModule):
    PARAMS = [
        ParameterDef('db_connection', is_required=True),
        ParameterDef('queries', is_required=True),
    ]

    def __init__(self, application):
        super().__init__(application)
        self.db_connection = {}
        self.queries = {}

    def serialize_state(self, state: object) -> [dict, None]:
        return json.dumps(state, cls=DecimalEncoder)

    def on_configured(self):
        connection_params = {k: self.db_connection[k] for k in self.db_connection.keys()}
        self.conn = psycopg2.connect(**connection_params, cursor_factory=RealDictCursor)

    def obtain_state(self, trigger) -> object:
        cur = self.conn.cursor()
        try:
            result = {}
            for name, query in self.queries.items():
                result[name] = []
                cur.execute(query)
                result[name] = [dict(x) for x in cur.fetchall()]
            return result
        finally:
            cur.close()
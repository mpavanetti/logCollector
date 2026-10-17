# Adding user role policies and index templates for Talend Remote Engine logs

We need those user role policies and index templates to assign mappings and rules for our created indexes.
Make sure you are running all these commands below in your elasticsearch cluster.

## Creating user role policy talendlog_writer for reading, writing and create indexes 
```
POST _security/role/talendlog_writer
{
  "cluster": ["manage_index_templates","monitor","manage_ingest_pipelines"], 
  "indices": [
    {
      "names": [ "talendlog-*" ], 
      "privileges": ["read","write","create_index"]
    }
  ]
}
```

## Role for ILM (Index Lifecycle Management) talendlog_ilm
```
POST _security/role/talendlog_ilm
{
  "cluster": ["manage_ilm"],
  "indices": [
    {
      "names": [ "talendlog-*","shrink-talendlog-*"],
      "privileges": ["write","create_index","manage","manage_ilm"]
    }
  ]
}
```

## Creating talendlog_internal user
```
POST /_security/user/talendlog_internal
{
  "password" : "<choose a strong password>",
  "roles" : [ "talendlog_writer","talendlog_ilm"],
  "full_name" : "Internal Talendlog User"
}
```

## ILM for deleting talend logs after a period of time.
The agent writes to monthly indexes itself, so the policy has no rollover (which needs a write alias the agent doesn't use, and left ILM stuck in an error before the delete phase): each index is deleted 67 days after it is created.
```
PUT _ilm/policy/talendlogs_policy   
{
  "policy": {                       
    "phases": {
      "delete": {
        "min_age": "67d",           
        "actions": {
          "delete": {}              
        }
      }
    }
  }
}
```

## Index template for Talend Resuming Logs (talendlog-resuming)
```
PUT /_template/talendlog-resuming
{
  "index_patterns": ["talendlog-resuming-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "index.lifecycle.name": "talendlogs_policy",
    "index.mapping.coerce": false
  }, 
  "mappings": {
    "properties": {
      "datetime": {
        "type": "date"
      },
      "pid": {
        "type": "keyword"
      },
      "type": {
        "type": "keyword"
      },
      "partName": {
        "type": "text"
      },
      "project": {
        "type": "keyword"
      },
      "jobName": {
        "type": "keyword"
      },
      "context": {
        "type": "keyword"
      },
      "jobVersion": {
        "type": "text"
      },
      "logPriority": {
        "type": "keyword"
      },
      "errorCode": {
        "type": "text"
      },
      "message": {
        "type": "text"
      },
      "duration": {
        "type": "text"
      },
      "result":{
        "type": "keyword"
      }
    }
  }
}
```

## Index template for Talend Studio Logs (talendlog-stdouterr)
```
PUT /_template/talendlog-stdouterr
{
  "index_patterns": ["talendlog-stdouterr-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "index.lifecycle.name": "talendlogs_policy",
    "index.mapping.coerce": false
  }, 
  "mappings": {
    "properties": {
      "datetime2": {
        "type": "date"
      },
      "pid": {
        "type": "keyword"
      },
      "jobName": {
        "type": "keyword"
      },
      "fileName": {
        "type": "keyword"
      },
      "studioLogs": {
        "type": "text"
      }
    }
  }
}
```

## Index template for Talend Task Logs (talendlog-task)
```
PUT /_template/talendlog-task
{
  "index_patterns": ["talendlog-task-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "index.lifecycle.name": "talendlogs_policy",
    "index.mapping.coerce": false
  }, 
  "mappings": {
    "properties": {
      "pid": {
        "type": "keyword"
      },
      "datetime": {
        "type": "date"
      },
      "jobName": {
        "type": "keyword"
      },
      "task_id": {
        "type": "keyword"
      },
      "task_execution_id": {
        "type": "keyword"
      },
      "remote_engine_id": {
        "type": "keyword"
      },
      "remote_engine_name": {
        "type": "keyword"
      },
      "workspace_name": {
        "type": "keyword"
      },
      "workspace_id": {
        "type": "keyword"
      },
      "environment_name": {
        "type": "keyword"
      },
      "environment_id": {
        "type": "keyword"
      },
      "environment_version": {
        "type": "keyword"
      },
      "trigger_timestamp": {
        "type": "date"
      },
      "artifact_name": {
        "type": "keyword"
      },
      "artifact_version": {
        "type": "text"
      },
      "task_name": {
        "type": "keyword"
      },
      "task_version": {
        "type": "text"
      },
      "run_type": {
        "type": "text"
      },
      "compatibility_version": {
        "type": "text"
      },
      "count_of_attempts": {
        "type": "text"
      },
      "taskLog": {
        "type": "text"
      }
    }
  }
}
```

### By Matheus Pavanetti - 2021
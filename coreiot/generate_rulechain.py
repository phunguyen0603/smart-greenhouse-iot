import uuid
import json

def generate_valid_rulechain():
    def make_id():
        return str(uuid.uuid4())

    node0_id = make_id()
    node1_id = make_id()
    node2_id = make_id()
    node3_id = make_id()
    node4_id = make_id()

    nodes = [
        {
            "id": {"entityType": "RULE_NODE", "id": node0_id},
            "createdTime": 0,
            "type": "org.thingsboard.rule.engine.filter.TbMsgTypeSwitchNode",
            "name": "Message Type Switch",
            "debugMode": False,
            "configurationVersion": 0,
            "configuration": {"version": 0},
            "additionalInfo": {
                "description": "Phân loại bản tin telemetry",
                "layoutX": 280,
                "layoutY": 250
            }
        },
        {
            "id": {"entityType": "RULE_NODE", "id": node1_id},
            "createdTime": 0,
            "type": "org.thingsboard.rule.engine.telemetry.TbMsgTimeseriesNode",
            "name": "Save Telemetry",
            "debugMode": False,
            "configurationVersion": 0,
            "configuration": {
                "defaultStorageTtl": 0
            },
            "additionalInfo": {
                "description": "Lưu telemetry vào CSDL chuỗi thời gian",
                "layoutX": 580,
                "layoutY": 150
            }
        },
        {
            "id": {"entityType": "RULE_NODE", "id": node2_id},
            "createdTime": 0,
            "type": "org.thingsboard.rule.engine.filter.TbJsFilterNode",
            "name": "Check TinyML Climate Risk",
            "debugMode": True,
            "configurationVersion": 0,
            "configuration": {
                "jsScript": "return (msg.tinyml_state === 1 || msg.tinyml_state === 2 || msg.temperature > 32.0 || msg.humidity > 90.0 || msg.thermal_shock_risk === true);"
            },
            "additionalInfo": {
                "description": "Kiểm tra rủi ro nhiệt ẩm hoặc nhãn TinyML",
                "layoutX": 580,
                "layoutY": 350
            }
        },
        {
            "id": {"entityType": "RULE_NODE", "id": node3_id},
            "createdTime": 0,
            "type": "org.thingsboard.rule.engine.action.TbCreateAlarmNode",
            "name": "Create Climate Alarm",
            "debugMode": False,
            "configurationVersion": 0,
            "configuration": {
                "alarmType": "Greenhouse Climate Alert",
                "alarmDetailsBuildJs": "var details = {};\ndetails.ai_state = msg.tinyml_state_str;\ndetails.temp = msg.temperature;\ndetails.humi = msg.humidity;\ndetails.vpd = msg.vpd;\ndetails.message = 'Climate risk detected by Edge AI!';\nreturn details;",
                "severity": "CRITICAL",
                "propagate": True,
                "propagateToOwner": False,
                "propagateToTenant": False,
                "useMessageAlarmData": False,
                "overwriteAlarmDetails": True
            },
            "additionalInfo": {
                "description": "Tạo cảnh báo trên CoreIOT",
                "layoutX": 880,
                "layoutY": 280
            }
        },
        {
            "id": {"entityType": "RULE_NODE", "id": node4_id},
            "createdTime": 0,
            "type": "org.thingsboard.rule.engine.rpc.TbSendRPCRequestNode",
            "name": "Auto Turn On Fan (RPC)",
            "debugMode": True,
            "configurationVersion": 0,
            "configuration": {
                "timeoutInSeconds": 10,
                "oneWayElseTwoWay": True,
                "requestBody": "{\n  \"method\": \"setFanState\",\n  \"params\": true\n}"
            },
            "additionalInfo": {
                "description": "Gửi lệnh RPC tự động bật quạt",
                "layoutX": 880,
                "layoutY": 420
            }
        }
    ]

    connections = [
        {"fromIndex": 0, "toIndex": 1, "type": "Post telemetry"},
        {"fromIndex": 0, "toIndex": 2, "type": "Post telemetry"},
        {"fromIndex": 2, "toIndex": 3, "type": "True"},
        {"fromIndex": 2, "toIndex": 4, "type": "True"}
    ]

    rule_chain_data = {
        "ruleChain": {
            "name": "Smart Greenhouse RuleChain (HK261)",
            "type": "CORE",
            "firstRuleNodeId": None,
            "root": False,
            "debugMode": False,
            "configuration": None,
            "additionalInfo": {
                "description": "Hệ thống RuleChain tự động hóa cho Smart Greenhouse (HK261)"
            }
        },
        "metadata": {
            "firstNodeIndex": 0,
            "nodes": nodes,
            "connections": connections,
            "ruleChainConnections": None
        }
    }

    with open(r"d:\BK\HK261\IoT\Assignment\coreiot\rulechain_greenhouse.json", "w", encoding="utf-8") as f:
        json.dump(rule_chain_data, f, indent=2, ensure_ascii=False)
    print("rulechain_greenhouse.json generated successfully!")

if __name__ == "__main__":
    generate_valid_rulechain()

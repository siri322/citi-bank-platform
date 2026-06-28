import os
from kubernetes import client, config
import requests

def check_pod_health():
    """
    Validates impacted pods, identifies CrashLoopBackOff, Pending, and sends notifications.
    """
    try:
        # Load local kubeconfig or incluster config if running inside a pod
        config.load_kube_config()
    except Exception as e:
        print(f"Failed to load kubernetes configuration: {e}")
        return

    v1 = client.CoreV1Api()
    
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
    except Exception as e:
        print(f"Error fetching pods: {e}")
        return

    unhealthy_pods = []
    
    for pod in pods.items:
        namespace = pod.metadata.namespace
        name = pod.metadata.name
        status = pod.status.phase
        
        # Check for non-running pods
        if status not in ["Running", "Succeeded"]:
            unhealthy_pods.append(f"[{namespace}] {name} - Status: {status}")
            continue
            
        # Check for container restarts (CrashLoopBackOff indication)
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if container.restart_count > 5:
                    unhealthy_pods.append(f"[{namespace}] {name} - CrashLoopBackOff (Restarts: {container.restart_count})")
                    
    if unhealthy_pods:
        alert_message = "Pod Health Issues Detected:\n" + "\n".join(unhealthy_pods)
        print(alert_message)
        send_slack_notification(alert_message)
    else:
        print("All pods are healthy.")

def send_slack_notification(message):
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not slack_webhook_url:
        print("SLACK_WEBHOOK_URL not set. Skipping Slack notification.")
        return
        
    payload = {
        "text": "*Kubernetes Health Alert*\n```\n" + message + "\n```"
    }
    
    try:
        response = requests.post(slack_webhook_url, json=payload)
        response.raise_for_status()
        print("Successfully sent Slack notification.")
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")

if __name__ == "__main__":
    check_pod_health()

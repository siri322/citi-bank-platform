import boto3
import os
import json
from datetime import datetime, timezone

def analyze_cost_optimization_opportunities():
    """
    Identifies unused EBS volumes, idle EC2 instances, and old snapshots.
    """
    ec2_client = boto3.client('ec2', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    opportunities = {
        'unused_ebs': [],
        'idle_ec2s': [],
        'old_snapshots': []
    }
    
    try:
        # Check Unused EBS Volumes
        volumes = ec2_client.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
        for volume in volumes.get('Volumes', []):
            opportunities['unused_ebs'].append({
                'VolumeId': volume['VolumeId'],
                'Size': volume['Size'],
                'VolumeType': volume['VolumeType']
            })
            
        # Check Idle EC2s (simplified check - stopped instances)
        # Note: True idle check would use CloudWatch metrics for CPU < 5% over 7 days
        instances = ec2_client.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
        for reservation in instances.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                opportunities['idle_ec2s'].append({
                    'InstanceId': instance['InstanceId'],
                    'InstanceType': instance['InstanceType']
                })
                
        # Check Old Snapshots (> 30 days)
        now = datetime.now(timezone.utc)
        snapshots = ec2_client.describe_snapshots(OwnerIds=['self'])
        for snapshot in snapshots.get('Snapshots', []):
            age_days = (now - snapshot['StartTime']).days
            if age_days > 30:
                opportunities['old_snapshots'].append({
                    'SnapshotId': snapshot['SnapshotId'],
                    'VolumeId': snapshot.get('VolumeId', 'Unknown'),
                    'AgeDays': age_days,
                    'VolumeSize': snapshot['VolumeSize']
                })
                
    except Exception as e:
        print(f"Error communicating with AWS: {e}")
        return

    report = "AWS Cost Optimization Report:\n"
    report += f"- Unused EBS Volumes: {len(opportunities['unused_ebs'])}\n"
    report += f"- Idle/Stopped EC2s: {len(opportunities['idle_ec2s'])}\n"
    report += f"- Old Snapshots (>30 days): {len(opportunities['old_snapshots'])}\n"
    
    print(report)
    
    if os.environ.get("SLACK_WEBHOOK_URL"):
        import requests
        payload = {"text": "*Cost Optimization Report*\n```\n" + report + "\n```"}
        try:
            requests.post(os.environ.get("SLACK_WEBHOOK_URL"), json=payload)
        except Exception as e:
            print(f"Failed to notify slack: {e}")

if __name__ == "__main__":
    # AWS credentials should be available in the environment
    # e.g., AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    analyze_cost_optimization_opportunities()

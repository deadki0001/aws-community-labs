import boto3
import datetime

# List of EC2 instances to exclude from termination
EXCLUDED_EC2_INSTANCES = {"i-06d382fbbc235cc86", "i-0e318c0f5e708e56b", "i-01838314e0290b3bc"}

# List of RDS instances to exclude from deletion
EXCLUDED_RDS_INSTANCES = {"deadki-us-db"}

def handler(event, context):
    now = datetime.datetime.utcnow()
    terminated_ec2_instances = []
    deleted_rds_instances = []

    # Get all AWS regions
    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    
    for region in regions:
        ec2 = boto3.client('ec2', region_name=region)
        rds = boto3.client('rds', region_name=region)

        try:
            # Terminate all EC2 instances except those in EXCLUDED_EC2_INSTANCES
            instances = ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    if instance_id not in EXCLUDED_EC2_INSTANCES:
                        ec2.terminate_instances(InstanceIds=[instance_id])
                        terminated_ec2_instances.append(f"{instance_id} (Region: {region})")
                    else:
                        print(f"Skipping EC2 instance {instance_id} (Region: {region})")

            # Delete all RDS instances except those in EXCLUDED_RDS_INSTANCES
            rds_instances = rds.describe_db_instances()
            for db_instance in rds_instances['DBInstances']:
                db_instance_id = db_instance['DBInstanceIdentifier']
                if db_instance_id not in EXCLUDED_RDS_INSTANCES:
                    rds.delete_db_instance(
                        DBInstanceIdentifier=db_instance_id,
                        SkipFinalSnapshot=True,  # Set to False if you need a final snapshot
                        DeleteAutomatedBackups=True
                    )
                    deleted_rds_instances.append(f"{db_instance_id} (Region: {region})")
                else:
                    print(f"Skipping RDS instance {db_instance_id} (Region: {region})")

        except Exception as e:
            print(f"Error processing region {region}: {e}")

    return {
        'statusCode': 200,
        'body': f"EC2 Terminated: {terminated_ec2_instances} | RDS Deleted: {deleted_rds_instances}"
    }

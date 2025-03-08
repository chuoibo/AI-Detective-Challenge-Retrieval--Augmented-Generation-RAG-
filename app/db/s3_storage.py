import boto3
import json
from datetime import datetime
from typing import Dict, Any
from app.core.config import settings
import uuid

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET
    
    def save_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_id = str(uuid.uuid4())[:8]
            
            query_slug = "".join(c if c.isalnum() else "_" for c in report_data["query"][:30])
            
            filename = f"report_{timestamp}_{query_slug}_{report_id}.json"
            
            report_json = json.dumps(report_data, indent=2)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=report_json,
                ContentType='application/json'
            )
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': filename
                },
                ExpiresIn=86400  
            )
            
            return {
                "success": True,
                "report_id": report_id,
                "filename": filename,
                "url": url,
                "timestamp": timestamp
            }
            
        except Exception as e:
            print(f"Error saving report to S3: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_reports(self, limit: int = 10) -> Dict[str, Any]:
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="report_",
                MaxKeys=limit
            )
            
            reports = []
            if "Contents" in response:
                for item in response["Contents"]:
                    url = self.s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': self.bucket_name,
                            'Key': item["Key"]
                        },
                        ExpiresIn=3600  
                    )
                    
                    reports.append({
                        "filename": item["Key"],
                        "last_modified": item["LastModified"].isoformat(),
                        "size": item["Size"],
                        "url": url
                    })
            
            return {
                "success": True,
                "reports": sorted(reports, key=lambda x: x["last_modified"], reverse=True)
            }
            
        except Exception as e:
            print(f"Error listing reports from S3: {e}")
            return {
                "success": False,
                "error": str(e),
                "reports": []
            }
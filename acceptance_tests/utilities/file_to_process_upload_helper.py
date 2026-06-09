import os
import time
import uuid

from requests_toolbelt import MultipartEncoder

from acceptance_tests.utilities import iap_requests
from acceptance_tests.utilities.test_case_helper import test_helper
from config import Config


def upload_and_process_file_by_api(collex_id, file_path, job_type, delete_after_upload=False):
    file_name = f'{job_type}_{str(uuid.uuid4())}.csv'

    file_id = upload_file_by_api(file_path, file_name)

    job_id = create_job(collex_id, file_name, file_id, job_type)

    wait_for_job_file_validation(job_id)

    process_job(job_id)

    if delete_after_upload:
        os.unlink(file_path)


def upload_file_by_api(file_path: str, file_name: str) -> str:
    multipart_data = MultipartEncoder(fields={
        'file': (file_name, open(file_path, 'rb'), 'text/plain')
    })

    url = f'{Config.SUPPORT_TOOL_API_URL}/upload'

    response = iap_requests.make_request(method='POST',
                                         url=url,
                                         headers={'Content-Type': multipart_data.content_type},
                                         data=multipart_data)
    response.raise_for_status()
    file_id = str(response.text.strip('"'))
    return file_id


def create_job(collex_id: str, file_name: str, file_id: str, job_type: str) -> str:
    request_params = {
        'fileId': file_id,
        'fileName': file_name,
        'collectionExerciseId': collex_id,
        'jobType': job_type
    }

    create_job_url = f'{Config.SUPPORT_TOOL_API_URL}/job'
    response = iap_requests.make_request(method='POST', url=create_job_url, params=request_params)
    response.raise_for_status()

    job_id = str(response.text.strip('"'))
    return job_id


def wait_for_job_file_validation(job_id: str, timeout_sec=30) -> None:
    get_job_url = f'{Config.SUPPORT_TOOL_API_URL}/job/{job_id}'

    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        response = iap_requests.make_request('GET', url=get_job_url)
        response.raise_for_status()

        if response.json().get("jobStatus") == "VALIDATED_OK":
            break
        else:
            time.sleep(1)
    else:  # Executes if the while condition is false, without breaking out of the loop
        test_helper.fail(f"File did not pass validation before timeout, job response: {response.json()}")


def process_job(job_id: str) -> None:
    process_job_url = f'{Config.SUPPORT_TOOL_API_URL}/job/{job_id}/process'
    response = iap_requests.make_request(method='POST', url=process_job_url)
    response.raise_for_status()

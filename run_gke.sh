#!/bin/bash
set -e

if [ -z "$ENV" ]; then
  echo "No ENV set. Using kubectl current context."

else
  GCP_PROJECT=census-rm-$ENV
  gcloud config set project "$GCP_PROJECT"
  gcloud container clusters get-credentials rm-k8s-cluster \
      --region europe-west2 \
      --project "$GCP_PROJECT"
fi

if [ "$NAMESPACE" ]; then
  kubectl config set-context "$(kubectl config current-context)" --namespace="$NAMESPACE"
  echo "NAMESPACE = [$NAMESPACE] Set kubectl namespace for subsequent commands [$NAMESPACE]."
fi


if [ "$REGRESSION" = "true" ]; then
  echo "Running with the regression tests"
else
  SKIP_REGRESSION_TAGS='--tags=~@regression'
  echo "Skipping regression tags"
  BEHAVE_TAGS="$BEHAVE_TAGS $SKIP_REGRESSION_TAGS"
fi

echo "Running with behave tags: \"$BEHAVE_TAGS\""

# Use the optional image tag argument, or default it to "latest"
IMAGE_TAG="${1:-latest}"
COMPLETE_MANIFEST="tmp_${IMAGE_TAG}_acceptance_tests_pod.yml"

echo "Using image tag [$IMAGE_TAG] and env [$ENV], saving manifest as \"$COMPLETE_MANIFEST\""

# Replace "$MANIFEST_IMAGE_TAG" in the target manifest with the value of IMAGE_TAG,
# And replace the "$ENV" with the value of ENV for environment specific values
# save the output to the tmp_manifests directory
sed -e "s/\$MANIFEST_IMAGE_TAG/$IMAGE_TAG/" -e "s/\$ENV/$ENV/" acceptance_tests_pod.yml > "$COMPLETE_MANIFEST"


kubectl delete pod acceptance-tests --wait || true

echo "Running RM Acceptance Tests [$(kubectl config current-context)]..."
kubectl apply -f "$COMPLETE_MANIFEST"

kubectl wait --for=condition=Ready pod/acceptance-tests --timeout=200s

kubectl exec -it acceptance-tests -- /bin/bash -c \
  "sleep 2;  python -m poll_endpoint --url https://support-tool-$ENV.rm.gcp.onsdigital.uk/actuator/health --max_retries 10"


kubectl exec -it acceptance-tests -- /bin/bash -c "sleep 2; behave acceptance_tests/features $BEHAVE_TAGS --tags=~@SupportFrontend --logging-level WARN"

kubectl delete pod acceptance-tests || true

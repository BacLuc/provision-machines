function ktx() {
  if [ $# -eq 0 ]; then
     kubectl config get-contexts
     return
  fi
  cat ${shell_tmp_dir}/.kube/config | yq '.current-context="'$1'"' | cat > ${shell_tmp_dir}/.kube/config
}

KUBECONFIG="$HOME/.kube/config.d/empty"
for file in $(find $HOME/.kube/config.d -type f); do
  KUBECONFIG="$KUBECONFIG:$file"
done

shell_tmp_dir=$(mktemp -d)
mkdir ${shell_tmp_dir}/.kube
yq eval -n ' .apiVersion="v1" | .current-context="" | .contexts=[] | .users=[] | .clusters=[] ' | cat  > ${shell_tmp_dir}/.kube/config
export KUBECONFIG="$KUBECONFIG:${shell_tmp_dir}/.kube/config"

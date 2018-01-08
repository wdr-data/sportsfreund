### Ansible Secrets

```bash
echo "<VAULT PASSWORD>" > .vault_password
ansible-vault create group_vars/all/vault.yml
```

```yaml
mongodb_url:
  staging: ""
redis_url:
  staging: ""
```

### Running Playbooks

```bash
aws configure --profile <MY PROFILE>
export AWS_PROFILE="<MY PROFILE>"
export KOPS_STATE_STORE=s3://<kops state store bucket>
kops export kubecfg <CLUSTER NAME>

ansible-playbook site.yml
```

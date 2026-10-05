import subprocess
import json
import unittest

def k8s_post(pod_index: int, path: str, payload: dict = None) -> dict:
    """Kalder en specifik Pod (0..N-1) inde i Kubernetes via kubectl exec."""
    cmd = [
        "kubectl", "exec", f"bully-{pod_index}", "--",
        "python", "-c",
        f"import urllib.request, json; "
        f"req = urllib.request.Request('http://localhost:5000{path}', "
        f"data=json.dumps({payload or {}}).encode(), "
        f"headers={{'Content-Type': 'application/json'}}, method='POST'); "
        f"print(urllib.request.urlopen(req).read().decode())"
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return json.loads(out)

class TestKubernetesSystem(unittest.TestCase):

    def setUp(self):
        # Gør P1..P5 (bully-0..4) levende og P6 (bully-5) crashed
        for i in range(5):
            k8s_post(i, "/control/crash", {"crashed": False})
        k8s_post(5, "/control/crash", {"crashed": True})

    def test_system_original_bully(self):
        # P2 (bully-1) starter original election -> Forventer Leader=5, Messages=12
        res = k8s_post(1, "/run/original")
        self.assertEqual((res["leader"], res["messages"]), (5, 12))

    def test_system_improved_bully(self):
        # P2 (bully-1) starter improved election -> Forventer Leader=5, Messages=7
        res = k8s_post(1, "/run/improved")
        self.assertEqual((res["leader"], res["messages"]), (5, 7))

if __name__ == "__main__":
    unittest.main(verbosity=2)

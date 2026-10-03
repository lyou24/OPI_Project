import sys
import os
import argparse
import asyncio
import subprocess

# プロジェクトルートパスの設定
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from app import fetch_and_analyze_user

DEFAULT_USER_IDS = [10605, 7381, 10870]

def run_git_push(updated_ids):
    """データベースの変更をコミットしてGitHubへプッシュする"""
    ids_str = ", ".join(str(uid) for uid in updated_ids)
    commit_msg = f"chore: ユーザー({ids_str})の最新スコアをローカル更新して反映"
    
    print(f"\n[Git] データベースのコミット・プッシュを開始します: {commit_msg}")
    
    try:
        # git add
        subprocess.run(["git", "add", "data/opi_database.sqlite"], cwd=PROJECT_DIR, check=True)
        
        # 差分があるか確認
        diff_check = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PROJECT_DIR)
        if diff_check.returncode == 0:
            print("[Git] データベースに変更はありませんでした（プッシュをスキップします）。")
            return True
            
        # git commit
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=PROJECT_DIR, check=True)
        
        # git push
        subprocess.run(["git", "push", "origin", "main"], cwd=PROJECT_DIR, check=True)
        print("[Git] GitHub (lyou24/OPI_Project) へのプッシュが正常に完了しました！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Git エラー] コマンド実行に失敗しました: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Ongeki OPI ユーザースコア取得・更新・自動プッシュスクリプト")
    parser.add_argument("user_ids", nargs="*", type=int, default=DEFAULT_USER_IDS,
                        help="更新対象のユーザーID（未指定時はデフォルト: 10605, 7381, 10870）")
    parser.add_argument("--no-push", action="store_true", help="GitHubへの自動プッシュをスキップする")
    
    args = parser.parse_args()
    target_ids = args.user_ids
    
    print(f"=== Ongeki OPI スコア更新バッチ ===")
    print(f"対象ユーザーID: {target_ids}")
    
    updated_ids = []
    for uid in target_ids:
        print(f"\n--> ユーザー {uid} のデータ取得を開始...")
        try:
            success = asyncio.run(fetch_and_analyze_user(uid, force=True))
            if success:
                print(f"[OK] ユーザー {uid} の更新に成功しました。")
                updated_ids.append(uid)
            else:
                print(f"[WARN] ユーザー {uid} の自動取得を完了できませんでした。")
        except Exception as e:
            print(f"[ERROR] ユーザー {uid} の更新中にエラーが発生しました: {e}", file=sys.stderr)
            
    print(f"\n=== 更新結果 ===")
    print(f"成功: {len(updated_ids)} / {len(target_ids)} 件 ({updated_ids})")
    
    if updated_ids and not args.no_push:
        run_git_push(updated_ids)
    elif not updated_ids:
        print("更新されたユーザーがないため、プッシュは行いません。")

if __name__ == "__main__":
    main()

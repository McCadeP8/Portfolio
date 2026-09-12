from fantrax_data import build_snapshot, save_snapshot


if __name__ == "__main__":
    snapshot = build_snapshot()
    save_snapshot(snapshot)
    print(
        f"Saved {sum(len(rows) for rows in snapshot['rosters'].values())} roster rows "
        f"across {len(snapshot['rosters'])} weeks."
    )

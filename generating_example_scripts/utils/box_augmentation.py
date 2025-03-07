import numpy as np
import pandas as pd

from utils.fast_hota_utils import calculate_box_ious

def add_random_boxes(df: pd.DataFrame):
    """
    For each unique frame in the dataframe, adds 2 new randomly placed boxes.
    
    Args:
        df: DataFrame with columns ['frame', 'id', 'bb_left', 'bb_top', 'bb_width', 'bb_height', 'conf', 'class', 'visibility']
    """
    if len(df) == 0:
        return
        
    # Get unique frames
    frames = df['frame'].unique()
    
    # For each frame, create 2 new random boxes
    new_rows = []
    
    for frame in frames:
        # Get frame dimensions from existing boxes
        frame_boxes = df[df['frame'] == frame]
        max_x = frame_boxes['bb_left'].max() + frame_boxes['bb_width'].max()
        max_y = frame_boxes['bb_top'].max() + frame_boxes['bb_height'].max()
        
        # Create 2 random boxes
        for _ in range(2):
            width = np.random.randint(30, 100)
            height = np.random.randint(30, 100)
            left = np.random.randint(0, max(1, max_x - width))
            top = np.random.randint(0, max(1, max_y - height))
            next_id = np.random.randint(0, 41)
            
            new_row = {
                'frame': frame,
                'id': next_id,
                'bb_left': left,
                'bb_top': top, 
                'bb_width': width,
                'bb_height': height,
                'conf': 1.0,
                'class': 1,
                'visibility': 1.0
            }
            new_rows.append(new_row)
            
    # Add new boxes to dataframe
    new_df = pd.DataFrame(new_rows)
    return pd.concat([df, new_df], ignore_index=True)


def drop_detections(df: pd.DataFrame, base_lambda: float = 0.05):
    if len(df) == 0:
        return

    to_drop_ids = list()
    frame_ids = df['frame'].unique().tolist()
    for frame in frame_ids:
        ids = df[df['frame'] == frame].index
        if len(ids) == 0:
            continue
        sub_df = df.loc[ids]
        bb1 = sub_df[['bb_left', 'bb_top', 'bb_width', 'bb_height']].values
        ious = calculate_box_ious(bb1, bb1)
        ious = ious - np.eye(len(sub_df))  # remove self-ious
        ious = np.max(ious, axis=-1)
        odds = ious * base_lambda
        drop_mask = np.random.rand(len(sub_df)) < odds
        drop_ids = ids[drop_mask]
        if len(drop_ids) > 0:
            to_drop_ids.extend(drop_ids.to_list())
    df.drop(to_drop_ids, inplace=True)


def inject_localization_error(df: pd.DataFrame, base_lambda: float = 0.05):
    if len(df) == 0:
        return

    frame_ids = df['frame'].unique().tolist()
    for frame in frame_ids:
        ids = df[df['frame'] == frame].index
        if len(ids) == 0:
            continue
        sub_df = df.loc[ids]
        bb1 = sub_df[['bb_left', 'bb_top', 'bb_width', 'bb_height']].values
        ious = calculate_box_ious(bb1, bb1)
        ious = ious - np.eye(len(sub_df))  # remove self-ious
        ious = np.max(ious, axis=-1)
        odds = ious * base_lambda
        mask = np.random.rand(len(sub_df)) < odds
        if mask.sum() == 0:
            continue
        jitter_value = np.random.randint(0, 10)

        g_idx = ids[mask]
        df.loc[g_idx, 'bb_left'] += np.random.normal(0, jitter_value, mask.sum()).astype(int)
        df.loc[g_idx, 'bb_top'] += np.random.normal(0, jitter_value, mask.sum()).astype(int)
        df.loc[g_idx, 'bb_width'] += np.random.normal(0, jitter_value, mask.sum()).astype(int)
        df.loc[g_idx, 'bb_height'] += np.random.normal(0, jitter_value, mask.sum()).astype(int)

        df.loc[g_idx, 'bb_width'] = np.maximum(df.loc[g_idx, 'bb_width'], 10)
        df.loc[g_idx, 'bb_height'] = np.maximum(df.loc[g_idx, 'bb_height'], 10)



def inject_label_swaps(df: pd.DataFrame, base_lambda: float = 0.05):
    if len(df) == 0:
        return

    frame_ids = df['frame'].unique().tolist()
    for frame in frame_ids:
        ids = df[df['frame'] == frame].index
        if len(ids) == 0:
            continue
        sub_df = df.loc[ids]
        bb1 = sub_df[['bb_left', 'bb_top', 'bb_width', 'bb_height']].values
        ious = calculate_box_ious(bb1, bb1)
        ious[np.tril_indices(len(ious))] = 0  # remove self-ious and everything below the diagonal as ious is symmetric
        odds = ious * base_lambda
        mask = np.random.rand(*ious.shape) < odds
        if mask.sum() == 0:
            continue

        # get the ids
        ann_ids = df['id'].values

        # find the i,j coordiantes of the nonzero elements of mask
        i, j = np.nonzero(mask)
        for k in range(len(i)):
            # swap labels i[k] and j[k]
            src_id = ann_ids[i[k]]
            tgt_id = ann_ids[j[k]]
            df.loc[df['id'] == src_id, 'id'] = tgt_id



def swap_labels(df: pd.DataFrame, a:int, b:int):
    idx_a = df['id'] == a
    idx_b = df['id'] == b
    if idx_a.sum() == 0 or idx_b.sum() == 0:
        print(f"swap_labels: {a} or {b} not found in df")

    df.loc[idx_a, 'id'] = b
    df.loc[idx_b, 'id'] = a
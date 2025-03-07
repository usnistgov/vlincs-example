import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from scipy.optimize import linear_sum_assignment



class CostMatrixData:
    # poor mans sparse array
    i_ids: np.ndarray  # Array of reference IDs for the y axis of the cost matrix
    j_ids: np.ndarray  # Array of comparison IDs for the x axis of the cost matrix
    cost_matrix: np.ndarray  # Cost matrix for the current clip
    video_id: str  # the video id
    frame: int  # the video frame number
    ref_id2idx_map: dict[int, int] = None
    comp_id2idx_map: dict[int, int] = None
    match_rows: np.ndarray = None
    match_cols: np.ndarray = None
    ref2comp_idx_map: dict[int, int] = None
    ref2comp_id_map: dict[int, int] = None

    def __init__(self, i_ids: np.ndarray, j_ids: np.ndarray, cost_matrix: np.ndarray, video_id: str, frame: int):
        self.i_ids = i_ids
        self.j_ids = j_ids
        self.cost_matrix = cost_matrix
        self.video_id = video_id
        self.frame = frame
        # lazily created to avoid unnecessary memory allocation and copy to parallel workers
        self._ref_id2idx_map = None
        self._comp_id2idx_map = None
        self._match_rows = None
        self._match_cols = None
        self._ref2comp_idx_map = None
        self._ref2comp_id_map = None

    def get_cost(self, i: int, j: int) -> float:
        """Get the cost matrix value at coordinate (i,j).

        Args:
            i: Reference ID (not index)
            j: Comparison ID (not index)

        Returns:
            Cost value at the specified coordinate
        """
        # Find indices of i,j in the id arrays
        i_idx = np.where(self.i_ids == i)[0]
        j_idx = np.where(self.j_ids == j)[0]

        # If either ID not found, return 0
        if len(i_idx) == 0 or len(j_idx) == 0:
            return np.nan
            # raise ValueError(f'ID not found in cost matrix: {i}, {j}')

        return float(self.cost_matrix[i_idx[0], j_idx[0]])
    
    def serialize(self, output_fp: str):
        import json
        assert output_fp.endswith('.json'), "output_fp must end with .json"
        res = {
            'i_ids': self.i_ids.tolist(),
            'j_ids': self.j_ids.tolist(),
            'cost_matrix': self.cost_matrix.tolist(),
            'video_id': self.video_id,
            'frame': self.frame
        }
        with open(output_fp, 'w') as f:
            json.dump(res, f, indent=2)
    
    @staticmethod
    def deserialize(input_fp: str) -> 'CostMatrixData':
        import json
        assert input_fp.endswith('.json'), "input_fp must end with .json"
        with open(input_fp, 'r') as f:
            res = json.load(f)
        for k, v in res.items():
            if isinstance(v, list):
                res[k] = np.array(v)
        return CostMatrixData(**res)
    
    
    def ref_id2idx(self, id: int) -> int:
        if self._ref_id2idx_map is None:
            self._ref_id2idx_map = {id: idx for idx, id in enumerate(self.i_ids)}
        return self._ref_id2idx_map[id]
    
    def comp_id2idx(self, id: int) -> int:
        if self._comp_id2idx_map is None:
            self._comp_id2idx_map = {id: idx for idx, id in enumerate(self.j_ids)}
        return self._comp_id2idx_map[id]
    
    def construct_id2idx_lookup(self) -> tuple[dict[int, int], dict[int, int]]:
        if self._ref_id2idx_map is None:
            self._ref_id2idx_map = {id: idx for idx, id in enumerate(self.i_ids)}
        if self._comp_id2idx_map is None:
            self._comp_id2idx_map = {id: idx for idx, id in enumerate(self.j_ids)}
    
    def construct_assignment(self):
        self.match_rows, self.match_cols = linear_sum_assignment(-self.cost_matrix)

        # Create mapping from GT ID to matched tracker ID
        self.ref2comp_idx_map = {self.match_rows[i]: self.match_cols[i] for i in range(len(self.match_rows))}
        a = self.i_ids[self.match_rows]
        b = self.j_ids[self.match_cols]
        self.ref2comp_id_map = {a[i]: b[i] for i in range(len(a))}
        
        


@dataclass
class Sparse2DMatrix:
    values: dict[tuple[int, int], float] = field(default_factory=dict)

    def add_at(self, i: int, j: int, v: float) -> None:
        key = (i, j)
        self.values[key] = self.values.get(key, 0) + v

    def get(self, i: int, j: int) -> float:
        return self.values.get((i, j), 0)

    def items(self) -> list[tuple[tuple[int, int], float]]:
        """Returns a list of (key, value) pairs, mimicking dict.items().
        
        Returns:
            List of tuples containing (key, value) pairs.
        """
        return list(self.values.items())
    
    def __iadd__(self, other: 'Sparse2DMatrix') -> 'Sparse2DMatrix':
        """Adds another Sparse2DMatrix to this one in-place.
        
        Args:
            other: Another Sparse2DMatrix to add to this one.
            
        Returns:
            Self, with values from other added.
        """
        # Add values from the other matrix to this one
        for (i,j), v in other.items():
            self.add_at(i, j, v)
        
        return self

@dataclass
class Sparse1DMatrix:
    values: dict[int, float] = field(default_factory=dict)

    def add_at(self, i: int, v: float) -> None:
        self.values[i] = self.values.get(i, 0) + v

    def get(self, i: int) -> float:
        return self.values.get(i, 0)
    
    def items(self) -> list[tuple[int, float]]:
        """Returns a list of (key, value) pairs, mimicking dict.items().
        
        Returns:
            List of tuples containing (key, value) pairs.
        """
        return list(self.values.items())
    
    def __iadd__(self, other: 'Sparse1DMatrix') -> 'Sparse1DMatrix':
        """Adds another Sparse1DMatrix to this one in-place.
        
        Args:
            other: Another Sparse1DMatrix to add to this one.
            
        Returns:
            Self, with values from other added.
        """
        # Add values from the other matrix to this one
        for i, v in other.items():
            self.add_at(i, v)
        
        return self


@dataclass
class FrameExtractionInputData:
    ref_df: pd.DataFrame
    comp_df: pd.DataFrame
    video_id: str  # the video id


@dataclass
class VideoFrameData:
    ref_np: np.ndarray  # reference video frame box numpy array with column names defined in col_names
    comp_np: np.ndarray  # comparison video frame box numpy array with column names defined in col_names
    video_id: str  # the video id
    frame: int  # the video frame number
    class_id: int
    col_names: list[str]

   



class HOTA_DATA_PRECURSOR:
    video_id: str
    frame: int
    TP: np.ndarray = None
    FN: np.ndarray = None
    FP: np.ndarray = None
    LocA: np.ndarray = None

    # sparse storage required to build the HOTA metric later
    matches_counts: list[Sparse2DMatrix]
    ref_id_counts: Sparse1DMatrix
    comp_id_counts: Sparse1DMatrix

    def __init__(self, video_id, frame):
        self.video_id = video_id
        self.frame = frame
        self.TP = np.zeros(len(HOTA_DATA.array_labels))
        self.FN = np.zeros(len(HOTA_DATA.array_labels))
        self.FP = np.zeros(len(HOTA_DATA.array_labels))
        self.LocA = np.zeros(len(HOTA_DATA.array_labels))
        
        self.matches_counts = [Sparse2DMatrix() for _ in HOTA_DATA.array_labels]
        self.ref_id_counts = Sparse1DMatrix()
        self.comp_id_counts = Sparse1DMatrix()

    def __iadd__(self, other: 'HOTA_DATA_PRECURSOR') -> 'HOTA_DATA_PRECURSOR':
        """Adds another HOTA_DATA_PRECURSOR to this one in-place.
        
        Args:
            other: Another HOTA_DATA_PRECURSOR to add to this one.
            
        Returns:
            Self, with values from other added.
        """
        self.TP += other.TP
        self.FN += other.FN
        self.FP += other.FP
        self.LocA += other.LocA
        for a in range(len(HOTA_DATA.array_labels)):
            self.matches_counts[a] += other.matches_counts[a]
        self.ref_id_counts += other.ref_id_counts
        self.comp_id_counts += other.comp_id_counts
        
        return self
        




class HOTA_DATA:
    # Static class variables that can be accessed directly from the class
    array_labels = np.arange(0.05, 0.99, 0.05)
    integer_array_fields = ['HOTA_TP', 'HOTA_FN', 'HOTA_FP']
    float_array_fields = ['HOTA', 'DetA', 'AssA', 'DetRe', 'DetPr', 'AssRe', 'AssPr', 'LocA', 'OWTA']
    array_fields = integer_array_fields + float_array_fields

    res: dict[str, np.ndarray]  # on demand storage for HOTA fields
    video_id: str


    def __init__(self, video_id):
        self.video_id = video_id
        

        self.res = dict()
        self.res['video_id'] = video_id
        for field in self.float_array_fields + self.integer_array_fields:
            self.res[field] = np.zeros((len(HOTA_DATA.array_labels)), dtype=float)

    def serialize(self, output_fp: str):
        import json, copy
        assert output_fp.endswith('.json'), "output_fp must end with .json"

        # validate that all the res fields are present
        for field in HOTA_DATA.array_fields:
            assert field in self.res, f"field {field} not found in res"
        # serialize the res dict to a json file
        res = copy.deepcopy(self.res)
        for k, v in res.items():
            if isinstance(v, np.ndarray):
                res[k] = v.tolist()
        with open(output_fp, 'w') as f:
            json.dump(res, f, indent=2)
    
    @staticmethod
    def deserialize(input_fp: str) -> 'HOTA_DATA':
        import json
        assert input_fp.endswith('.json'), "input_fp must end with .json"
        # deserialize the res dict from a json file
        dat = HOTA_DATA(video_id='')
        with open(input_fp, 'r') as f:
            res = json.load(f)
        for k, v in res.items():
            if isinstance(v, list):
                res[k] = np.array(v)
        # validate that all the res fields are present
        for field in HOTA_DATA.array_fields:
            assert field in res, f"field {field} not found in res"
        dat.video_id = res['video_id']
        dat.res = res
        return dat

    def populate(self, pre_hota_data: HOTA_DATA_PRECURSOR, id_cost_matrix: CostMatrixData):

        ref_id_counts = np.zeros((len(id_cost_matrix.i_ids), 1))
        comp_id_counts = np.zeros((1, len(id_cost_matrix.j_ids)))
        
        # instantiate the dense version of ref_id_counts and comp_id_counts
        for k, v in pre_hota_data.ref_id_counts.items():
            i = id_cost_matrix.ref_id2idx(k)
            ref_id_counts[i, 0] += v
        for k, v in pre_hota_data.comp_id_counts.items():
            j = id_cost_matrix.comp_id2idx(k)
            comp_id_counts[0, j] += v

        # Copy over the TP, FN, FP, LocA from pre_hota_data
        self.res['HOTA_TP'] = pre_hota_data.TP
        self.res['HOTA_FN'] = pre_hota_data.FN
        self.res['HOTA_FP'] = pre_hota_data.FP
        self.res['LocA'] = pre_hota_data.LocA

        for a, alpha in enumerate(HOTA_DATA.array_labels):
            # instantiate the dense version of matches_count
            matches_count = np.zeros((len(id_cost_matrix.i_ids), len(id_cost_matrix.j_ids)))
            for k, v in pre_hota_data.matches_counts[a].values.items():
                matches_count[id_cost_matrix.ref_id2idx(k[0]), id_cost_matrix.comp_id2idx(k[1])] = v

            ass_a = matches_count / np.maximum(1, ref_id_counts + comp_id_counts - matches_count)
            self.res['AssA'][a] = np.sum(matches_count * ass_a) / np.maximum(1, self.res['HOTA_TP'][a])
            ass_re = matches_count / np.maximum(1, ref_id_counts)
            self.res['AssRe'][a] = np.sum(matches_count * ass_re) / np.maximum(1, self.res['HOTA_TP'][a])
            ass_pr = matches_count / np.maximum(1, comp_id_counts)
            self.res['AssPr'][a] = np.sum(matches_count * ass_pr) / np.maximum(1, self.res['HOTA_TP'][a])

        # Calculate final scores
        self.res['LocA'] = np.maximum(1e-10, self.res['LocA']) / np.maximum(1e-10, self.res['HOTA_TP'])
        self.finalize()
        
    def finalize(self):
        self.res['DetRe'] = self.res['HOTA_TP'] / np.maximum(1, self.res['HOTA_TP'] + self.res['HOTA_FN'])
        self.res['DetPr'] = self.res['HOTA_TP'] / np.maximum(1, self.res['HOTA_TP'] + self.res['HOTA_FP'])
        self.res['DetA'] = self.res['HOTA_TP'] / np.maximum(1, self.res['HOTA_TP'] + self.res['HOTA_FN'] + self.res['HOTA_FP'])
        self.res['HOTA'] = np.sqrt(self.res['DetA'] * self.res['AssA'])
        self.res['OWTA'] = np.sqrt(self.res['DetRe'] * self.res['AssA'])
        

    @staticmethod  # stolen from trackeval
    def _combine_weighted_av(all_res, field, comb_res, weight_field):
        """Combine sequence results via weighted average"""
        return sum([all_res[k][field] * all_res[k][weight_field] for k in all_res.keys()]) / np.maximum(1.0, comb_res[
            weight_field])

    @staticmethod
    def merge(all_dat: dict[str, 'HOTA_DATA']) -> 'HOTA_DATA':
        # """Combines metrics across all sequences"""
        
        if len(all_dat) == 0:
            raise ValueError("all_res must contain at least one HOTA_DATA object")
        if len(all_dat) == 1:
            return list(all_dat.values())[0]

        # get the first key
        dat = HOTA_DATA(video_id='COMBINED_SEQ')  # from trackeval
        # package like TrackEval code wants
        # this gets a naked dict of the res from each HOTA_DATA object
        all_res = {k: v.res for k, v in all_dat.items()}
        for field in dat.integer_array_fields:
            if field not in dat.res:
                dat.res[field] = 0
            for h in all_res.values():
                dat.res[field] += h[field]
        
        for field in ['AssRe', 'AssPr', 'AssA']:
            dat.res[field] = HOTA_DATA._combine_weighted_av(all_res, field, dat.res, weight_field='HOTA_TP')

        loca_weighted_sum = sum([all_res[k]['LocA'] * all_res[k]['HOTA_TP'] for k in all_res.keys()])
        dat.res['LocA'] = np.maximum(1e-10, loca_weighted_sum) / np.maximum(1e-10, dat.res['HOTA_TP'])
        dat.finalize()

        return dat


MAKEFLAGS += --no-builtin-rules

all: predict

# general definitions
UID=$(shell id -u)
GID=$(shell id -g)
DOCKER = docker
DOCKER_RUN = $(DOCKER) run --gpus all --ipc=host --tty --interactive --rm
DOCKER_UID = --user $(UID)

PWD = $(shell pwd)

# MMDetection specific

MMDETECTION_IMAGE = local/mmdetection:v2.17.0

MMDETECTION_ID = $(shell docker images -q $(MMDETECTION_IMAGE))
MMDETECTION_EXISTS = $(shell if test -n "$(MMDETECTION_ID)"; then echo ""; else echo "mmdetection-docker"; fi)

# YOLO specific

YOLO_IMAGE = ultralytics/yolov5:v4.0  # 5.0

# YOLO configuration
YOLO_TYPE = yolov5l
YOLO_WEIGHTS = $(YOLO_TYPE).pt
YOLO_WEIGHTS_URL = https://github.com/ultralytics/yolov5/releases/download/v4.0/$(YOLO_WEIGHTS)

# YOLO docker internal definitions
YOLO_DIR = /usr/src/app
YOLO_MOUNTS = -v "$(PWD)/generated/synthcells:$(YOLO_DIR)/data/synthcells" \
			  -v "$(PWD)/generated/realcells:$(YOLO_DIR)/data/realcells" \
			  -v "$(PWD)/generated/yolo-runs:$(YOLO_DIR)/runs" \
			  -v "$(PWD)/generated/yolo-weights/$(YOLO_WEIGHTS):$(YOLO_DIR)/$(YOLO_WEIGHTS)"

# content of yolo data configuration yaml
define YOLO_SYNTHCELLS_YAML
train: data/synthcells/YOLOOutput-synthcells/
val: data/synthcells/YOLOOutput-synthcells/

# number of classes
nc: 1

# class names
names: ['cell']
endef
export YOLO_SYNTHCELLS_YAML

define YOLO_REALCELLS_YAML
train: data/realcells/train
val: data/realcells/val

# number of classes
nc: 1

# class names
names: ['cell']
endef
export YOLO_REALCELLS_YAML


define MMDETECTION_CONFIG
_base_ = [
    '../../configs/mask_rcnn/mask_rcnn_r50_fpn_1x_coco.py'
]

classes=('cell',)
num_classes = len(classes)

model = dict(
    roi_head=dict(
        bbox_head=dict(
            num_classes=num_classes
        ),
        mask_head=dict(
            num_classes=num_classes
        )
    ),
    test_cfg=dict(
        rpn=dict(
            nms_pre=12000,
            max_per_img=4000,
        ),
        rcnn=dict(
            score_thr=0.5,
            max_per_img=3000,
		)
    )
)

dataset_root = 'data/synthcells/COCOOutput-synthcells/'
dataset_val_root = 'data/realcells/'

# update data pipeline
data = dict(
    samples_per_gpu=2,
    workers_per_gpu=10,
    train=dict(
        classes=classes,
        ann_file=dataset_root + 'annotations.json',
        img_prefix=dataset_root + 'train',
    ),
    val=dict(
        classes=classes,
        ann_file=dataset_val_root + 'annotations.json',
        img_prefix=dataset_val_root + 'val',
    ),
    test=dict(
        classes=classes,
        ann_file=dataset_val_root + 'annotations.json',
        img_prefix=dataset_val_root + 'test',
    )
)

# pretrained weights
load_from = "https://download.openmmlab.com/mmdetection/v2.0/mask_rcnn/mask_rcnn_r50_fpn_2x_coco/mask_rcnn_r50_fpn_2x_coco_bbox_mAP-0.392__segm_mAP-0.354_20200505_003907-3e542a40.pth"

# save checkpoint every epoch
checkpoint_config = dict(interval=1)
# perform evaluation every epoch
evaluation = dict(interval=1, metric=['bbox', 'segm'], proposal_nums=[100, 1500, 3000])
endef
export MMDETECTION_CONFIG

generated/synthcells/YOLOOutput-synthcells/classes.txt: generated/synthcells/cellsium-has-run

generated/synthcells/yolo-synthcells.yaml: generated/synthcells/YOLOOutput-synthcells/classes.txt
	echo "$$YOLO_SYNTHCELLS_YAML" > $@


generated/realcells/yolo-realcells.yaml: generated/realcells/val/000000000000.txt
	echo "$$YOLO_REALCELLS_YAML" > $@

generated/yolo-weights/$(YOLO_WEIGHTS):
	mkdir -p generated/yolo-weights/
	wget $(YOLO_WEIGHTS_URL) -O $@

generated/yolo-runs/train/exp/weights/best.pt: generated/yolo-weights/$(YOLO_WEIGHTS) generated/synthcells/yolo-synthcells.yaml generated/realcells/yolo-realcells.yaml
	mkdir -p generated/yolo-runs
	-$(DOCKER_RUN) $(YOLO_MOUNTS) \
		$(YOLO_IMAGE) \
		python train.py --cfg models/$(YOLO_TYPE).yaml --weights '$(YOLO_WEIGHTS)' --data data/synthcells/yolo-synthcells.yaml 2>&1 | tee generated/yolo-train.log
	$(DOCKER_RUN) $(YOLO_MOUNTS) \
		alpine:3.12.4 \
		chown -R $(UID):$(GID) $(YOLO_DIR)


generated/yolo-runs/test/exp/test_batch0_labels.jpg: generated/yolo-runs/train/exp/weights/best.pt
	$(DOCKER_RUN) $(YOLO_MOUNTS) \
		$(YOLO_IMAGE) \
		python test.py --data data/realcells/yolo-realcells.yaml --weights runs/train/exp/weights/best.pt --conf-thres 0.001 --iou-thres 0.6 --verbose --single-cls --save-txt --save-conf 2>&1 | tee generated/yolo-predict.log
	$(DOCKER_RUN) $(YOLO_MOUNTS) \
		alpine:3.12.4 \
		chown -R $(UID):$(GID) $(YOLO_DIR)

# unfortunately no official image, so we build it locally
mmdetection-docker:
	$(DOCKER) build -t $(MMDETECTION_IMAGE) "https://github.com/open-mmlab/mmdetection.git#v2.17.0:docker"
	
MMDETECTION_DIR = /mmdetection

MMDETECTION_MOUNTS = -v "$(PWD)/generated/synthcells:$(MMDETECTION_DIR)/data/synthcells" \
					 -v "$(PWD)/generated/realcells:$(MMDETECTION_DIR)/data/realcells" \
					 -v "$(PWD)/generated/mmdetection-work_dirs:$(MMDETECTION_DIR)/work_dirs"

generated/synthcells/mask_rcnn.py: generated/synthcells/COCOOutput-synthcells/annotations.json
	echo "$$MMDETECTION_CONFIG" > $@
	
generated/mmdetection-work_dirs/mask_rcnn/latest.pth: $(MMDETECTION_EXISTS) generated/synthcells/mask_rcnn.py generated/realcells/val/000000000000.txt
	-$(DOCKER_RUN) $(MMDETECTION_MOUNTS) $(MMDETECTION_IMAGE) \
	python tools/train.py data/synthcells/mask_rcnn.py 2>&1 | tee generated/mmdetection-train.log
	$(DOCKER_RUN) $(MMDETECTION_MOUNTS) \
		alpine:3.12.4 \
		chown -R $(UID):$(GID) $(MMDETECTION_DIR)

generated/mmdetection-work_dirs/mask_rcnn/test_out.pkl: generated/mmdetection-work_dirs/mask_rcnn/latest.pth
	-$(DOCKER_RUN) $(MMDETECTION_MOUNTS) $(MMDETECTION_IMAGE) \
	python tools/test.py data/synthcells/mask_rcnn.py work_dirs/mask_rcnn/latest.pth --out work_dirs/mask_rcnn/test_out.pkl 2>&1 | tee generated/mmdetection-predict.log
	$(DOCKER_RUN) $(MMDETECTION_MOUNTS) \
		alpine:3.12.4 \
		chown -R $(UID):$(GID) $(MMDETECTION_DIR)


CELLSIUM_IMAGE = ghcr.io/modsim/cellsium
CELLSIUM_ID = $(shell docker images -q $(CELLSIUM_IMAGE))
CELLSIUM_EXISTS = $(shell if test -n "$(CELLSIUM_ID)"; then echo ""; else echo "cellsium-docker"; fi)

cellsium-docker:
	$(DOCKER) build -t $(CELLSIUM_IMAGE) git@github.com:modsim/CellSium.git#main
    
generated/synthcells/cellsium-has-run: $(CELLSIUM_EXISTS)
	mkdir -p generated/synthcells
	$(DOCKER_RUN) $(DOCKER_UID) -v "$(PWD)/generated/synthcells:/output" \
	--entrypoint python \
	$(CELLSIUM_IMAGE) \
	-m cellsium training -t TrainingDataCount=50 -t TrainingCellCount=512 -t TrainingImageWidth=512 -t TrainingImageHeight=512 -t Calibration=0.0905158 -t ChipmunkPlacementRadius=0.01 \
	-o /output/synthcells --Output COCOOutput --Output YOLOOutput --Output GenericMaskOutput -p
	touch generated/synthcells/cellsium-has-run

generated/realcells/val/000000000000.txt: $(CELLSIUM_EXISTS)
	mkdir -p generated/realcells/
	$(DOCKER_RUN) $(DOCKER_UID) -v "$(PWD)/generated/realcells:/output" -v "$(PWD)/prepare.py:/tmp/prepare.py" -v "$(PWD)/realcells.tif:/tmp/realcells.tif" \
	--entrypoint python \
	$(CELLSIUM_IMAGE) \
	/tmp/prepare.py /tmp/realcells.tif /output
	cp -R "$(PWD)/generated/realcells/train" "$(PWD)/generated/realcells/val"
	cp -R "$(PWD)/generated/realcells/train" "$(PWD)/generated/realcells/test"

.PHONY: yolo-train yolo-predict mmdetection-docker maskrcnn-train maskrcnn-predict cellsium-docker cellsium-generate realcells-generate
yolo-train: generated/yolo-runs/train/exp/weights/best.pt
yolo-predict: generated/yolo-runs/test/exp/test_batch0_labels.jpg
maskrcnn-train: generated/mmdetection-work_dirs/mask_rcnn/latest.pth
maskrcnn-predict: generated/mmdetection-work_dirs/mask_rcnn/test_out.pkl
cellsium-generate: generated/synthcells/cellsium-has-run
realcells-generate: generated/realcells/val/000000000000.txt
predict: yolo-predict maskrcnn-predict
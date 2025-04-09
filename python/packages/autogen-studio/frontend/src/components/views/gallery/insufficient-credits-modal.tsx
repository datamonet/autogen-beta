import React from "react";
import { Modal, Button } from "antd";

interface InsufficientCreditsModalProps {
  open: boolean;
  onHide: () => void;
}

export const InsufficientCreditsModal: React.FC<InsufficientCreditsModalProps> = ({
  open,
  onHide,
}) => {
  return (
    <Modal
      title={null}
      open={open}
      onCancel={onHide}
      footer={null}
      width={500}
    >
      <div className={"text-[18px] font-semibold leading-[27px]"}>
        Insufficient Credits
      </div>
      <div className="flex items-center justify-between py-4">
        <div className={"text-base leading-[24px]"}>
          <div>
            You've used all your credits. Please upgrade your plan to continue
            using our services.
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <Button onClick={onHide}>Cancel</Button>
        <Button
          type="primary"
          onClick={() => {
            onHide();
            window.open(`${process.env.NEXT_PUBLIC_TAKIN_API_URL}/pricing`, "_blank");
          }}
        >
          Upgrade Now
        </Button>
      </div>
    </Modal>
  );
};

export default InsufficientCreditsModal;
